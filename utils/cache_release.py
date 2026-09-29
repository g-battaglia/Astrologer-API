"""Aggregate libephemeris page-cache release after calculation activity."""

from __future__ import annotations

import asyncio
import logging
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from .ephemeris_readiness import is_ephemeris_ready_latched


logger = logging.getLogger(__name__)
CACHE_RELEASE_IDLE_S = float(os.environ.get("CACHE_RELEASE_IDLE_S", "5"))
if not math.isfinite(CACHE_RELEASE_IDLE_S) or CACHE_RELEASE_IDLE_S < 0:
    raise RuntimeError("CACHE_RELEASE_IDLE_S must be a finite number >= 0")

_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cache-release")
_state_lock = threading.Lock()
_active_calculations = 0
_activity_generation = 0


def calculation_started() -> None:
    global _active_calculations, _activity_generation
    with _state_lock:
        _active_calculations += 1
        _activity_generation += 1


def calculation_finished() -> None:
    global _active_calculations, _activity_generation
    with _state_lock:
        _active_calculations = max(0, _active_calculations - 1)
        _activity_generation += 1


def activity_snapshot() -> tuple[int, int]:
    with _state_lock:
        return _active_calculations, _activity_generation


def release_cache() -> None:
    """Best-effort blocking advisory call; execute only in `_EXECUTOR`."""
    if not is_ephemeris_ready_latched():
        return
    try:
        import libephemeris as ephe

        reader = ephe.get_leb_reader()
        if reader:
            reader.cool()
        ephe.release_data_cache()
    except Exception:
        logger.debug("Page-cache release failed", exc_info=False)


async def cache_release_loop(stop: asyncio.Event) -> None:
    """Release once after an idle period, never inline with a response."""
    loop = asyncio.get_running_loop()
    # Generation zero means that no calculation has run yet. Treat the current
    # generation as already released so startup alone never triggers a cache
    # advisory call; only subsequent calculation activity can schedule one.
    _, initial_generation = activity_snapshot()
    released_generation = 0 if initial_generation == 0 else -1
    while not stop.is_set():
        active, generation = activity_snapshot()
        if active or generation == released_generation:
            try:
                await asyncio.wait_for(stop.wait(), timeout=max(CACHE_RELEASE_IDLE_S, 0.001))
            except TimeoutError:
                continue
            break

        try:
            await asyncio.wait_for(stop.wait(), timeout=max(CACHE_RELEASE_IDLE_S, 0.001))
            break
        except TimeoutError:
            pass
        current_active, current_generation = activity_snapshot()
        if current_active == 0 and current_generation == generation:
            await loop.run_in_executor(_EXECUTOR, release_cache)
            released_generation = generation
