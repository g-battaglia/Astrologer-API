"""Sanitize configured ephemeris source failures at public boundaries."""

from __future__ import annotations

from typing import Any


_SOURCE_ERROR_NAMES = frozenset(
    {
        "CoefficientSourceError",
        "CoefficientSourceDataError",
        "CoefficientDataError",
    }
)


def _source_error_types() -> tuple[type[BaseException], ...]:
    """Return source-error classes exposed by the installed engine."""
    try:
        import libephemeris as ephe
    except Exception:  # pragma: no cover - the API cannot normally start without it
        return ()

    error_type = getattr(ephe, "CoefficientSourceError", ())
    return (error_type,) if isinstance(error_type, type) else ()


def _is_data_error(exc: BaseException) -> bool:
    """Identify a provider's explicit data-integrity failure, if supplied."""
    return bool(
        getattr(exc, "data_error", False)
        or getattr(exc, "is_data_error", False)
        or type(exc).__name__ in {"CoefficientSourceDataError", "CoefficientDataError"}
    )


def source_failure(exc: BaseException) -> tuple[int, dict[str, Any]] | None:
    """Map a source failure found anywhere in an exception cause chain.

    Configured source availability failures are temporary service failures. A
    provider may mark an integrity/data failure with ``data_error`` (or expose
    one of the conventional data-error class names); those failures are server
    errors instead. Both explicit causes and implicit contexts are visited, and
    cycles are ignored.
    """
    source_types = _source_error_types()
    if not source_types:
        return None

    pending = [exc]
    seen: set[int] = set()
    unavailable: tuple[int, dict[str, Any]] | None = None
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if cause is not None:
            pending.append(cause)
        if context is not None:
            pending.append(context)

        if not isinstance(current, source_types) and type(current).__name__ not in _SOURCE_ERROR_NAMES:
            continue

        if _is_data_error(current):
            return 500, {
                "status": "ERROR",
                "message": "Ephemeris source data is unavailable or invalid. The failure has been logged.",
                "error_type": "CoefficientSourceError",
            }
        unavailable = (
            503,
            {
                "status": "ERROR",
                "message": "Ephemeris source is temporarily unavailable. Retry after a short delay.",
                "error_type": "CoefficientSourceError",
            },
        )
    return unavailable
