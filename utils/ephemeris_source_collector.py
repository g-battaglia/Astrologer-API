"""
Ephemeris source collector — captures libephemeris backend information.

Uses libephemeris's ContextVar-based tracing to record which sub-backend
(LEB, Skyfield, Horizons, SPK, ASSIST, Keplerian) computed each celestial
body during a chart calculation.

Design constraints:
- Zero overhead when not in use (ContextVar check ~50ns per body).
- No log-level manipulation, no regex, no handler attachment.
- Thread-safe and async-safe via ContextVar.
"""

from __future__ import annotations

from contextvars import Token
from typing import Dict, Optional

import libephemeris

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


class EphemerisSourceCollector:
    """
    Context manager that captures ephemeris backend sources via libephemeris tracing.

    Usage::

        collector = EphemerisSourceCollector()
        with collector:
            # ... chart calculations ...
            pass
        sources = collector.get_sources()
        # {"Sun": "LEB", "Moon": "Skyfield", "Chiron": "SPK", ...}

    When not used (no ``with`` block entered), zero overhead.
    """

    __slots__ = ("_token", "_raw_results")

    def __init__(self) -> None:
        self._token: Optional[Token] = None
        self._raw_results: Dict[int, str] = {}

    def __enter__(self) -> "EphemerisSourceCollector":
        self._token = libephemeris.start_tracing()
        return self

    def __exit__(self, *exc: object) -> bool:
        # Snapshot results before resetting the ContextVar
        self._raw_results = libephemeris.get_trace_results()
        if self._token is not None:
            self._token.var.reset(self._token)
        return False

    def get_sources(self) -> Dict[str, str]:
        """Return ``{point_name: backend}`` for every body observed.

        Works both inside the ``with`` block (reads live from ContextVar)
        and after exit (reads from snapshot taken in ``__exit__``).
        """
        raw = self._raw_results or libephemeris.get_trace_results()
        return {_resolve_body_name(body_id): source for body_id, source in raw.items()}
