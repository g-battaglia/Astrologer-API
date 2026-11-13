"""
Ephemeris source collector — captures libephemeris backend information.

Request-local accumulation bridges native thread-local traces from calculation
workers. Completed subject provenance supplies sources from Kerykeion's nested
trace scopes, which do not merge into their native parent. No providers are
inferred from configuration, filenames or precomputed request payloads.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from threading import Lock
from typing import Any, Callable, Dict

import libephemeris
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Ephemeris body-ID → human-readable name
# Keys are the body IDs reported by libephemeris tracing. Values are API-facing
# body labels, not backend/source labels such as LEB, Skyfield or SPK.
# ---------------------------------------------------------------------------
_BODY_NAMES: Dict[int, str] = {
    -1: "Ecliptic_Nutation",  # ECL_NUT: nutation + obliquity (ERFA backend)
    0: "Sun",
    1: "Moon",
    2: "Mercury",
    3: "Venus",
    4: "Mars",
    5: "Jupiter",
    6: "Saturn",
    7: "Uranus",
    8: "Neptune",
    9: "Pluto",
    10: "Mean_North_Lunar_Node",
    11: "True_North_Lunar_Node",
    12: "Mean_Lilith",
    13: "True_Lilith",
    14: "Earth",
    15: "Chiron",
    16: "Pholus",
    17: "Ceres",
    18: "Pallas",
    19: "Juno",
    20: "Vesta",
    21: "Interpolated_Lilith",
    22: "Interpolated_Perigee",
    40: "Cupido",
    41: "Hades",
    42: "Zeus",
    43: "Kronos",
    44: "Apollon",
    45: "Admetos",
    46: "Vulkanus",
    47: "Poseidon",
    48: "Transpluto",
    56: "White_Moon",
}

_AST_OFFSET = 10_000

# TNO minor-planet catalogue numbers → names
_TNO_NUMBERS: Dict[int, str] = {
    136199: "Eris",
    90377: "Sedna",
    136108: "Haumea",
    136472: "Makemake",
    28978: "Ixion",
    90482: "Orcus",
    50000: "Quaoar",
}


def _resolve_body_name(body_id: int) -> str:
    """Resolve an ephemeris body ID to a human-readable point name."""
    name = _BODY_NAMES.get(body_id)
    if name is not None:
        return name
    if body_id > _AST_OFFSET:
        tno_name = _TNO_NUMBERS.get(body_id - _AST_OFFSET)
        if tno_name is not None:
            return tno_name
    return f"body_{body_id}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _merge_sources(target: Dict[str, str], sources: Dict[str, str]) -> None:
    for name, source in sources.items():
        previous = target.get(name)
        target[name] = source if previous is None or previous == source else "Mixed"


class EphemerisSourceCollector:
    """Synchronous native trace; enter and exit on the calculating thread."""

    def __init__(self) -> None:
        self._token: Any = None
        self._context_token: Token | None = None
        self._sources: Dict[str, str] = {}
        self._reported: Dict[str, str] = {}

    def __enter__(self) -> "EphemerisSourceCollector":
        self._sources = {}
        self._reported = {}
        self._token = libephemeris.start_tracing()
        self._context_token = _WORKER_COLLECTOR.set(self)
        return self

    def __exit__(self, *exc: object) -> bool:
        try:
            self._sources = self.get_sources()
        finally:
            try:
                if self._token is not None:
                    self._token.reset()
            finally:
                self._token = None
                if self._context_token is not None:
                    _WORKER_COLLECTOR.reset(self._context_token)
                    self._context_token = None
        return False

    def get_sources(self) -> Dict[str, str]:
        """Owned snapshot; an exited empty collector never reads another scope."""
        if self._token is None:
            return dict(self._sources)
        sources = {_resolve_body_name(body): source for body, source in libephemeris.get_trace_results().items()}
        _merge_sources(sources, self._reported)
        return sources


class EphemerisRequestSources:
    """Async-safe request scope, with no native token on the event-loop thread."""

    def __init__(self) -> None:
        self._context_token: Token | None = None
        self._sources: Dict[str, str] = {}
        self._lock = Lock()

    def __enter__(self) -> "EphemerisRequestSources":
        self._context_token = _REQUEST_SOURCES.set(self)
        return self

    def __exit__(self, *exc: object) -> bool:
        if self._context_token is not None:
            _REQUEST_SOURCES.reset(self._context_token)
            self._context_token = None
        return False

    def merge(self, sources: Dict[str, str]) -> None:
        # A cancelled request can leave an admitted worker finishing later.
        with self._lock:
            _merge_sources(self._sources, sources)

    def get_sources(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._sources)


_REQUEST_SOURCES: ContextVar[EphemerisRequestSources | None] = ContextVar("ephemeris_request_sources", default=None)
_WORKER_COLLECTOR: ContextVar[EphemerisSourceCollector | None] = ContextVar("ephemeris_worker_collector", default=None)


def run_with_ephemeris_sources(fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """Collect only opted-in work, on its worker, and publish even after failure."""
    request_sources = _REQUEST_SOURCES.get()
    if request_sources is None:
        return fn(*args, **kwargs)
    collector = EphemerisSourceCollector()
    try:
        with collector:
            return fn(*args, **kwargs)
    finally:
        request_sources.merge(collector.get_sources())


def record_subject_sources(subject: BaseModel) -> None:
    """Retain engine provenance immediately after a subject was computed.

    Native nested traces are isolated. Use their reported point sources, never
    guessed labels or serialized precomputed input. With debug off no model
    traversal or serialization is performed.
    """
    collector = _WORKER_COLLECTOR.get()
    if collector is None:
        return

    def visit(value: Any) -> None:
        if isinstance(value, BaseModel):
            name, source = getattr(value, "name", None), getattr(value, "source", None)
            if isinstance(name, str) and isinstance(source, str) and source != "Derived":
                _merge_sources(collector._reported, {name: source})
            for field in type(value).model_fields:
                visit(getattr(value, field))
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    visit(subject)
