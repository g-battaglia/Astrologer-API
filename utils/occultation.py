"""Shared occultation-search helpers for REST and MCP.

Native searches can outlive a Python thread timeout. Each search therefore
runs in a dedicated spawned subprocess, terminated and then killed when it
exceeds its budget. The subprocess also exits after every completed search,
releasing its memory.
"""

from __future__ import annotations

import asyncio
import math
import multiprocessing
import os
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
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
    """Reconstruct the child's exception so ``handle_exception`` keeps its
    status mapping: KerykeionException/OverflowError/ValueError -> 400 paths,
    anything else -> generic 500."""
    if name == "KerykeionException":
        from kerykeion.schemas import KerykeionException

        return KerykeionException(msg)
    if name == "OverflowError":
        return OverflowError(msg)
    if name == "ValueError":
        return ValueError(msg)
    return RuntimeError(msg)


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
