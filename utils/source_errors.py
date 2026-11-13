"""Sanitize configured ephemeris source failures at public boundaries."""

from __future__ import annotations

from typing import Any


def source_failure(exc: BaseException) -> tuple[int, dict[str, Any]] | None:
    """Find source failures in wrapper causes without exposing driver messages."""
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if type(current).__name__ == "CoefficientSourceError":
            return 503, {
                "status": "ERROR",
                "message": "Ephemeris source is temporarily unavailable. Retry after a short delay.",
                "error_type": "CoefficientSourceError",
            }
        pending.extend(item for item in (current.__cause__, current.__context__) if item is not None)
    return None
