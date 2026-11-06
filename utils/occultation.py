"""Shared occultation-search helpers for REST and MCP.

Native searches can outlive a Python thread timeout. Each search therefore
runs in a spawned subprocess, terminated and then killed when it exceeds its
budget. Optional prewarmed workers retain immutable readers across successful
searches; failed or cancelled workers are discarded and replaced. The default
one-shot path remains available when persistent workers are not enabled.
"""

from __future__ import annotations

import asyncio
import math
import logging
import multiprocessing
import os
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

from .heavy_work import ServerBusyError

# Occulted-body name -> Swiss Ephemeris planet id. The request models / MCP tool
# restrict `planet` to these names, so lookups never fall through to a silent
# default.
OCCULTATION_PLANET_IDS: dict[str, int] = {
    "Sun": 0,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
}

# Hard ceilings for native searches that cannot be interrupted in-process.
OCCULTATION_SEARCH_TIMEOUT_S = 120.0
HELIACAL_SEARCH_TIMEOUT_S = 180.0

# How many isolated native-search subprocesses may run concurrently. Each worker
# peaks at ~200-360 MB RSS (kerykeion + numpy/astropy + ephemeris mmap), so the
# default serializes these rare endpoints to avoid OOM on a memory-limited
# instance. At most one additional request may wait, and only briefly: the
# native-search timeout starts after execution admission, so an unbounded queue
# could otherwise consume the SDK's complete request timeout before calculating.
NATIVE_SEARCH_MAX_PROCS = int(os.environ.get("NATIVE_SEARCH_MAX_PROCS", os.environ.get("OCCULTATION_MAX_PROCS", "1")))
NATIVE_SEARCH_MAX_QUEUED = int(os.environ.get("NATIVE_SEARCH_MAX_QUEUED", "1"))
NATIVE_SEARCH_QUEUE_TIMEOUT_S = float(os.environ.get("NATIVE_SEARCH_QUEUE_TIMEOUT_S", "2"))
if not 1 <= NATIVE_SEARCH_MAX_PROCS <= 8:
    raise RuntimeError("NATIVE_SEARCH_MAX_PROCS must be between 1 and 8")
if not 0 <= NATIVE_SEARCH_MAX_QUEUED <= 32:
    raise RuntimeError("NATIVE_SEARCH_MAX_QUEUED must be between 0 and 32")
if not math.isfinite(NATIVE_SEARCH_QUEUE_TIMEOUT_S) or not 0.05 <= NATIVE_SEARCH_QUEUE_TIMEOUT_S <= 120:
    raise RuntimeError("NATIVE_SEARCH_QUEUE_TIMEOUT_S must be a finite number between 0.05 and 120")
_NATIVE_SEARCH_CAPACITY = NATIVE_SEARCH_MAX_PROCS + NATIVE_SEARCH_MAX_QUEUED

# Grace period after SIGTERM before escalating to SIGKILL.
_TERMINATE_GRACE_S = 3.0

# spawn (not fork): fork from an async server with threads + libephemeris's
# module-level RLock is unsafe; spawn is the portable safe choice (and the
# macOS default). spawn copies os.environ to the child, so LIBEPHEMERIS_* data
# discovery works with no explicit env passing.
_MP_CONTEXT = multiprocessing.get_context("spawn")

# Dedicated pool for the blocking pipe-wait so the default ``to_thread`` pool is
# never parked for the full timeout. Sized to the process cap so a waiter never
# queues behind a parked poll thread.
_NATIVE_IO_EXECUTOR = ThreadPoolExecutor(max_workers=NATIVE_SEARCH_MAX_PROCS, thread_name_prefix="native-wait")
# Cancellation can arrive while every wait thread is parked in `_wait_for_result`.
# Reaping on that same saturated executor would queue terminate/kill behind the
# original timeout, leaving the native process alive after its client vanished.
_NATIVE_REAP_EXECUTOR = ThreadPoolExecutor(max_workers=NATIVE_SEARCH_MAX_PROCS, thread_name_prefix="native-reap")

# asyncio.Semaphore is loop-bound on first use; cache one capacity pair per
# running loop so tests that spin up multiple loops (asyncio.run) don't trip
# "bound to a different event loop". The token queue provides strict, immediate
# admission: only running + configured queued requests hold a token, while any
# excess request gets ServerBusy without joining another hidden queue. The
# execution semaphore bounds live subprocesses and its wait is timed. Weak keys
# (not id(loop)) prevent a recycled address from inheriting stale capacity.
_NATIVE_ADMISSION_QUEUES: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Queue[None]]" = weakref.WeakKeyDictionary()
_NATIVE_EXECUTION_SEMAPHORES: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = weakref.WeakKeyDictionary()
_NATIVE_POOLS: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, _NativeSearchPool]" = weakref.WeakKeyDictionary()
_logger = logging.getLogger(__name__)


def _get_capacity(loop: asyncio.AbstractEventLoop) -> tuple[asyncio.Queue[None], asyncio.Semaphore]:
    admission = _NATIVE_ADMISSION_QUEUES.get(loop)
    execution = _NATIVE_EXECUTION_SEMAPHORES.get(loop)
    if admission is None or execution is None:
        admission = asyncio.Queue(maxsize=_NATIVE_SEARCH_CAPACITY)
        for _ in range(_NATIVE_SEARCH_CAPACITY):
            admission.put_nowait(None)
        execution = asyncio.Semaphore(NATIVE_SEARCH_MAX_PROCS)
        _NATIVE_ADMISSION_QUEUES[loop] = admission
        _NATIVE_EXECUTION_SEMAPHORES[loop] = execution
    return admission, execution


async def _acquire_before(semaphore: asyncio.Semaphore, deadline: float) -> None:
    remaining = deadline - asyncio.get_running_loop().time()
    if remaining <= 0:
        raise TimeoutError
    await asyncio.wait_for(semaphore.acquire(), timeout=remaining)


def _occultation_worker(send_conn: Any, kind: str, kwargs: dict) -> None:
    """Runs in the spawned child: import kerykeion lazily, search, send result.

    Sends ``("ok", events)`` or ``("err", exc_class_name, str(exc))``. Imports
    kerykeion *inside* the function so importing this module in the child stays
    stdlib-light.
    """
    try:
        from kerykeion import OccultationFactory

        factory = OccultationFactory()
        if kind == "local":
            events = factory.search_local(**kwargs)
        elif kind == "global":
            events = factory.search_global(**kwargs)
        else:
            raise ValueError(f"unknown occultation kind: {kind!r}")
        send_conn.send(("ok", events))
    except BaseException as exc:  # never let the child hang the parent on a result
        send_conn.send(("err", type(exc).__name__, str(exc)))
    finally:
        send_conn.close()


def _heliacal_worker(send_conn: Any, kind: str, kwargs: dict) -> None:
    """Build the subject and execute the complete heliacal search in one child."""
    try:
        from kerykeion import AstrologicalSubjectFactory, HeliacalFactory

        subject_kwargs = kwargs.pop("subject_kwargs")
        subject = AstrologicalSubjectFactory.from_birth_data(**subject_kwargs)
        events = HeliacalFactory().search_events(
            julian_day=subject.julian_day,
            geopos=(subject.lng, subject.lat, getattr(subject, "altitude", 0) or 0),
            **kwargs,
        )
        send_conn.send(("ok", events))
    except BaseException as exc:
        send_conn.send(("err", type(exc).__name__, str(exc)))
    finally:
        send_conn.close()


def _sleep_forever_worker(send_conn: Any, kind: str, kwargs: dict) -> None:  # pragma: no cover - runs in child
    """Test seam: simulate a search that never returns (exercises timeout->kill)."""
    try:
        time.sleep(3600)
    finally:
        send_conn.close()


def _crash_worker(send_conn: Any, kind: str, kwargs: dict) -> None:  # pragma: no cover - runs in child
    """Test seam: die without sending (exercises the child-death path)."""
    os._exit(1)


def _wait_for_result(recv_conn: Any, proc: Any, timeout: float) -> tuple[str, Any]:
    """Block (in a worker thread) until the child sends a result, dies, or the
    timeout elapses. Returns ``("recv", payload)`` / ``("dead", None)`` /
    ``("timeout", None)``. Uses a short poll interval so it stays responsive and
    notices child death promptly."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if recv_conn.poll(0.5):
            try:
                return ("recv", recv_conn.recv())
            except (EOFError, OSError):  # peer closed without a full message -> crashed
                return ("dead", None)
        if not proc.is_alive():
            return ("dead", None)
    return ("timeout", None)


def _reap(proc: Any, recv_conn: Any, send_conn: Any) -> None:
    """Guarantee the child is gone and fds are closed. SIGTERM may not land on a
    process deep in one native call, so escalate to SIGKILL after a grace join."""
    try:
        if proc.is_alive():
            proc.terminate()
            proc.join(_TERMINATE_GRACE_S)
            if proc.is_alive():
                proc.kill()
                proc.join()
        else:
            proc.join()  # reap a finished child
    except (ValueError, AssertionError, OSError):  # e.g. never started
        pass
    finally:
        for conn in (recv_conn, send_conn):
            try:
                conn.close()
            except OSError:
                pass


def _rebuild_exception(name: str, msg: str) -> BaseException:
    """Reconstruct the child's exception so public status mapping is retained."""
    if name == "CoefficientSourceError":
        class CoefficientSourceError(Exception):
            pass

        return CoefficientSourceError("Ephemeris coefficient source failure")
    if name == "KerykeionException":
        from kerykeion.schemas import KerykeionException

        return KerykeionException(msg)
    if name == "OverflowError":
        return OverflowError(msg)
    if name == "ValueError":
        return ValueError(msg)
    return RuntimeError(msg)


def native_search_reuse_enabled() -> bool:
    value = os.environ.get("NATIVE_SEARCH_REUSE", "false").strip().lower()
    if value not in {"true", "false", "1", "0", "yes", "no"}:
        raise RuntimeError("NATIVE_SEARCH_REUSE must be a boolean")
    return value in {"true", "1", "yes"}


def _warm_native_search_runtime() -> None:
    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.ephemeris_backend.backend import BACKEND_NAME, ephe

    if BACKEND_NAME == "libephemeris":
        # Authenticate the complete selected inventory in the serving child.
        # Warming only the web process cannot warm a spawned interpreter.
        ephe.get_leb_inventory()
    AstrologicalSubjectFactory.from_birth_data(
        name="warmup", year=2000, month=1, day=1, hour=12, minute=0,
        lng=0.0, lat=51.48, tz_str="Etc/UTC", online=False,
        suppress_geonames_warning=True,
    )


def _cool_native_search_runtime() -> None:
    from kerykeion.ephemeris_backend.backend import BACKEND_NAME, ephe

    cool = getattr(ephe, "cool_leb_readers", None)
    if BACKEND_NAME == "libephemeris" and callable(cool):
        # Retain authenticated readers/digests and bounded decoded coefficients.
        # close()/reload would repeat the whole-image acquisition next time.
        cool(clear_coefficients=False)


class _ReusableResultSink:
    def __init__(self, connection: Any):
        self.connection = connection
        self.ok = False

    def send(self, result: tuple) -> None:
        self.ok = result[0] == "ok"
        self.connection.send(result)

    def close(self) -> None:
        # The existing one-shot workers close their result sink. The persistent
        # loop owns this connection and closes it after its final job instead.
        pass


def _native_search_worker_loop(connection: Any, initializer: Callable | None = None, worker: Callable | None = None) -> None:
    try:
        (initializer or _warm_native_search_runtime)()
        connection.send(("ok", None))
        while True:
            kind, kwargs = connection.recv()
            target = worker or (_heliacal_worker if kind == "heliacal" else _occultation_worker)
            sink = _ReusableResultSink(connection)
            target(sink, kind, kwargs)
            del kwargs
            if not sink.ok:
                return  # The parent discards this child after any job failure.
            if worker is None:
                try:
                    _cool_native_search_runtime()
                except Exception:
                    # Page-cache advice is best effort, unlike initial integrity
                    # verification. Never turn an already returned result into
                    # an unsolicited second protocol message.
                    pass
    except (EOFError, BrokenPipeError, OSError):
        pass
    except BaseException as error:
        try:
            connection.send(("err", type(error).__name__, str(error)))
        except (BrokenPipeError, OSError):
            pass
    finally:
        connection.close()


@dataclass(eq=False)
class _RetainedWorker:
    process: Any
    connection: Any
    child_connection: Any
    reap: asyncio.Future | None = None


def _pooled_exchange(worker: _RetainedWorker, kind: str, kwargs: dict, timeout: float) -> tuple:
    # IPC writes can block too. Keep serialization/write and wait off the event
    # loop; the parent's independent wall-clock watchdog covers both phases.
    started = time.monotonic()
    try:
        worker.connection.send((kind, kwargs))
        return _wait_for_result(worker.connection, worker.process, max(0.0, timeout - (time.monotonic() - started)))
    except (OSError, ValueError):
        return ("dead", None)


def _consume_background_failure(future: asyncio.Future) -> None:
    if not future.cancelled():
        future.exception()


class _NativeSearchPool:
    def __init__(self, *, initializer: Callable | None = None, worker: Callable | None = None):
        self.initializer = initializer
        self.worker = worker
        self.available: asyncio.Queue[_RetainedWorker] = asyncio.Queue()
        self.live: set[_RetainedWorker] = set()
        self.tasks: set[asyncio.Task] = set()
        self.start_task: asyncio.Task | None = None
        self.close_task: asyncio.Task | None = None
        self.ready = False
        self.closed = False
        self.owners = 0

    async def _discard(self, worker: _RetainedWorker) -> None:
        if worker.reap is None:
            worker.reap = asyncio.get_running_loop().run_in_executor(
                _NATIVE_REAP_EXECUTOR, _reap, worker.process, worker.connection, worker.child_connection,
            )
        cancelled = False
        while not worker.reap.done():
            try:
                await asyncio.shield(worker.reap)
            except asyncio.CancelledError:
                cancelled = True
        worker.reap.result()
        self.live.discard(worker)
        if cancelled:
            raise asyncio.CancelledError

    async def _create(self) -> _RetainedWorker:
        parent, child = _MP_CONTEXT.Pipe(duplex=True)
        process = _MP_CONTEXT.Process(target=_native_search_worker_loop, args=(child, self.initializer, self.worker), daemon=True)
        retained = _RetainedWorker(process, parent, child)
        self.live.add(retained)
        try:
            process.start()
            child.close()
            future = asyncio.get_running_loop().run_in_executor(_NATIVE_IO_EXECUTOR, _wait_for_result, parent, process, HELIACAL_SEARCH_TIMEOUT_S)
            future.add_done_callback(_consume_background_failure)
            outcome = await asyncio.wait_for(asyncio.shield(future), HELIACAL_SEARCH_TIMEOUT_S)
            if outcome[0] != "recv" or outcome[1][0] != "ok":
                raise RuntimeError("Native search worker warmup failed")
            return retained
        except BaseException:
            await self._discard(retained)
            raise

    async def _start(self) -> None:
        # Reserve the existing execution budget while warming: optional startup
        # traffic cannot create another set of native processes alongside it.
        _, execution = _get_capacity(asyncio.get_running_loop())
        acquired = 0
        pending: list[asyncio.Task] = []
        try:
            for _ in range(NATIVE_SEARCH_MAX_PROCS):
                await execution.acquire()
                acquired += 1
            pending = [asyncio.create_task(self._create()) for _ in range(NATIVE_SEARCH_MAX_PROCS)]
            for retained in await asyncio.gather(*pending):
                self.available.put_nowait(retained)
            self.ready = True
        except BaseException:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            await asyncio.gather(*(self._discard(w) for w in list(self.live)))
            raise
        finally:
            for _ in range(acquired):
                execution.release()

    async def start(self) -> None:
        if self.start_task is None:
            self.start_task = asyncio.create_task(self._start())
            self.start_task.add_done_callback(_consume_background_failure)
        await asyncio.shield(self.start_task)

    async def _recover(self) -> None:
        delay = 1.0
        while not self.closed:
            try:
                worker = await self._create()
                if self.closed:
                    await self._discard(worker)
                else:
                    self.available.put_nowait(worker)
                return
            except asyncio.CancelledError:
                raise
            except Exception as error:
                _logger.warning("Native search worker recovery failed (%s)", type(error).__name__)
                await asyncio.sleep(delay)
                delay = min(30.0, delay * 2)

    async def run(self, kind: str, kwargs: dict, timeout: float) -> list:
        try:
            worker = self.available.get_nowait()
        except asyncio.QueueEmpty as error:
            raise ServerBusyError("Native search workers are recovering; retry later.") from error
        successful = False
        try:
            if not worker.process.is_alive():
                raise ServerBusyError("Native search worker is recovering; retry later.")
            future = asyncio.get_running_loop().run_in_executor(_NATIVE_IO_EXECUTOR, _pooled_exchange, worker, kind, kwargs, timeout)
            future.add_done_callback(_consume_background_failure)
            outcome = await asyncio.wait_for(asyncio.shield(future), timeout)
            if outcome[0] == "timeout":
                raise TimeoutError("Native search exceeded its time budget")
            if outcome[0] == "dead":
                raise RuntimeError("Native search worker exited before returning a result")
            result = outcome[1]
            if result[0] != "ok":
                raise _rebuild_exception(result[1], result[2])
            successful = True
            return result[1]
        finally:
            if successful and not self.closed:
                self.available.put_nowait(worker)
            else:
                try:
                    await self._discard(worker)
                finally:
                    if not self.closed:
                        task = asyncio.create_task(self._recover())
                        self.tasks.add(task)
                        task.add_done_callback(self.tasks.discard)

    async def _close(self) -> None:
        self.closed = True
        self.ready = False
        pending = [*self.tasks, *([self.start_task] if self.start_task else [])]
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        await asyncio.gather(*(self._discard(w) for w in list(self.live)))
        while not self.available.empty():
            self.available.get_nowait()

    async def close(self) -> None:
        # Lifespan cancellation must not abandon recovery/startup children.
        # Share one complete cleanup even when multiple owners are cancelled.
        if self.close_task is None:
            self.close_task = asyncio.create_task(self._close())
        cancelled = False
        while not self.close_task.done():
            try:
                await asyncio.shield(self.close_task)
            except asyncio.CancelledError:
                cancelled = True
        self.close_task.result()
        if cancelled:
            raise asyncio.CancelledError


def acquire_native_search_pool() -> _NativeSearchPool | None:
    if not native_search_reuse_enabled():
        return None
    loop = asyncio.get_running_loop()
    pool = _NATIVE_POOLS.get(loop)
    if pool is None:
        pool = _NativeSearchPool()
        _NATIVE_POOLS[loop] = pool
    pool.owners += 1
    return pool


async def release_native_search_pool(pool: _NativeSearchPool | None) -> None:
    if pool is None:
        return
    pool.owners -= 1
    if pool.owners == 0:
        _NATIVE_POOLS.pop(asyncio.get_running_loop(), None)
        await pool.close()


async def run_occultation_search(kind: str, *, timeout: float, _worker: Callable | None = None, **kwargs: Any) -> list:
    """Run one native search with bounded waiting and a killable subprocess.

    Admission and execution must both complete within the shared queue deadline;
    otherwise ``ServerBusyError`` is raised before a subprocess starts. The
    search's own ``timeout`` begins only after execution admission. ``_worker``
    is a private test seam and must be a module-level, picklable target.
    """
    loop = asyncio.get_running_loop()
    target = _worker if _worker is not None else _occultation_worker
    admission, execution = _get_capacity(loop)
    deadline = loop.time() + NATIVE_SEARCH_QUEUE_TIMEOUT_S
    try:
        admission.get_nowait()
    except asyncio.QueueEmpty as exc:
        raise ServerBusyError("Native search capacity is busy; retry later.") from exc

    try:
        await _acquire_before(execution, deadline)
    except TimeoutError as exc:
        admission.put_nowait(None)
        raise ServerBusyError("Native search capacity is busy; retry later.") from exc
    except BaseException:
        admission.put_nowait(None)
        raise

    try:
        pool = _NATIVE_POOLS.get(loop)
        if pool is not None and pool.ready and target in {_occultation_worker, _heliacal_worker}:
            return await pool.run(kind, kwargs, timeout)
        recv_conn, send_conn = _MP_CONTEXT.Pipe(duplex=False)
        proc = _MP_CONTEXT.Process(target=target, args=(send_conn, kind, kwargs), daemon=True)
        try:
            proc.start()
            send_conn.close()  # parent never sends -> lets the child's exit surface as EOF
            outcome = await loop.run_in_executor(_NATIVE_IO_EXECUTOR, _wait_for_result, recv_conn, proc, timeout)
            if outcome[0] == "timeout":
                raise TimeoutError("Occultation search exceeded its time budget")
            if outcome[0] == "dead":
                raise RuntimeError("Occultation worker exited before returning a result")
            payload = outcome[1]
            if payload[0] == "ok":
                return payload[1]
            raise _rebuild_exception(payload[1], payload[2])
        finally:
            reap = loop.run_in_executor(_NATIVE_REAP_EXECUTOR, _reap, proc, recv_conn, send_conn)
            try:
                await asyncio.shield(reap)
            except asyncio.CancelledError:
                # `shield` protects the reap future but cancellation still exits
                # the await immediately. Wait for termination before releasing
                # either capacity slot.
                await reap
                raise
    finally:
        execution.release()
        admission.put_nowait(None)


async def run_heliacal_search(*, timeout: float = HELIACAL_SEARCH_TIMEOUT_S, _worker: Callable | None = None, **kwargs: Any) -> list:
    """Run a complete heliacal calculation in the shared killable process budget."""
    target = _worker if _worker is not None else _heliacal_worker
    return await run_occultation_search("heliacal", timeout=timeout, _worker=target, **kwargs)
