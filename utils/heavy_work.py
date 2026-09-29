"""Bounded admission and execution for synchronous calculation work."""

from __future__ import annotations

import asyncio
import contextvars
import functools
import math
import os
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from .cache_release import calculation_finished, calculation_started


class ServerBusyError(RuntimeError):
    """The bounded heavy-work queue could not admit another calculation."""


_default_workers = min(8, max(4, os.cpu_count() or 4))
HEAVY_MAX_WORKERS = int(os.environ.get("HEAVY_MAX_WORKERS", "") or _default_workers)
HEAVY_MAX_QUEUED = int(os.environ.get("HEAVY_MAX_QUEUED", "") or HEAVY_MAX_WORKERS * 4)
HEAVY_QUEUE_TIMEOUT_S = float(os.environ.get("HEAVY_QUEUE_TIMEOUT_S", "") or 2.0)

if not 1 <= HEAVY_MAX_WORKERS <= 32:
    raise RuntimeError("HEAVY_MAX_WORKERS must be between 1 and 32")
if not 0 <= HEAVY_MAX_QUEUED <= 256:
    raise RuntimeError("HEAVY_MAX_QUEUED must be between 0 and 256")
if not math.isfinite(HEAVY_QUEUE_TIMEOUT_S) or not 0.05 <= HEAVY_QUEUE_TIMEOUT_S <= 120:
    raise RuntimeError("HEAVY_QUEUE_TIMEOUT_S must be a finite number between 0.05 and 120")

_EXECUTOR = ThreadPoolExecutor(max_workers=HEAVY_MAX_WORKERS, thread_name_prefix="heavy")
_CAPACITY = HEAVY_MAX_WORKERS + HEAVY_MAX_QUEUED
_SEMAPHORES: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = weakref.WeakKeyDictionary()


def _semaphore(loop: asyncio.AbstractEventLoop) -> asyncio.Semaphore:
    semaphore = _SEMAPHORES.get(loop)
    if semaphore is None:
        semaphore = asyncio.Semaphore(_CAPACITY)
        _SEMAPHORES[loop] = semaphore
    return semaphore


async def run_heavy(fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """Run one calculation after bounded, timed queue admission.

    Cancellation of the awaiting coroutine does not stop a running Python
    thread. Its admission slot is released only by the executor future's done
    callback, never merely because the client disconnected.
    """
    loop = asyncio.get_running_loop()
    semaphore = _semaphore(loop)
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=HEAVY_QUEUE_TIMEOUT_S)
    except TimeoutError as exc:
        raise ServerBusyError("Heavy calculation capacity is busy; retry later.") from exc

    ctx = contextvars.copy_context()
    call = functools.partial(ctx.run, fn, *args, **kwargs)
    calculation_started()
    try:
        future = loop.run_in_executor(_EXECUTOR, call)
    except BaseException:
        calculation_finished()
        semaphore.release()
        raise

    released = False

    def release_slot(_future: asyncio.Future) -> None:
        nonlocal released
        # A cancelled request stops awaiting the shielded future, but its Python
        # thread keeps running. If that thread later raises, explicitly retrieve
        # the exception so asyncio cannot emit an unhandled-future traceback with
        # request data outside the privacy-safe error boundary. Retrieval does not
        # suppress propagation to a caller that is still awaiting the future.
        if not _future.cancelled():
            _future.exception()
        if not released:
            released = True
            calculation_finished()
            semaphore.release()

    future.add_done_callback(release_slot)
    return await asyncio.shield(future)
