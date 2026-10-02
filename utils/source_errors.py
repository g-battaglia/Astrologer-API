"""Sanitized coefficient-source failures shared by REST, MCP and subprocesses."""

from __future__ import annotations

from typing import Any


def source_failure(exc: BaseException) -> tuple[int, dict[str, Any]] | None:
    """Recognize backend failures, including a factory's causal wrapper.

    Args:
        exc: Original or wrapped backend exception.

    Returns:
        HTTP status and safe envelope, or None for non-source failures.
    """
    import libephemeris as ephe

    db_error = getattr(ephe, "DBError", ())
    db_data_error = getattr(ephe, "DBDataError", ())
    routing_error = getattr(ephe, "RoutingDataError", ())
    configuration_error = getattr(ephe, "ConfigurationError", ())
    network_error = getattr(ephe, "NetworkSealedError", ())
    seen: set[int] = set()
    pending = [exc]
    unavailable: tuple[int, dict[str, Any]] | None = None
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        # Wrappers can have both explicit causes and implicit contexts. A
        # generic availability wrapper must not downgrade a nested data fault.
        for cause in (current.__context__, current.__cause__):
            if cause is not None:
                pending.append(cause)
        if isinstance(current, configuration_error):
            return 500, {
                "status": "ERROR",
                "message": "Ephemeris source configuration is invalid. The failure has been logged.",
                "error_type": "NetworkSealedError" if isinstance(current, network_error) else "ConfigurationError",
            }
        if isinstance(current, db_error) or isinstance(current, routing_error):
            data_fault = isinstance(current, db_data_error) or isinstance(current, routing_error)
            failure = (500 if data_fault else 503), {
                "status": "ERROR",
                "message": (
                    "Ephemeris source data is unavailable or invalid. The failure has been logged." if data_fault else "Ephemeris source is temporarily unavailable. Retry after a short delay."
                ),
                "error_type": "RoutingDataError" if isinstance(current, routing_error) else "DBDataError" if data_fault else "DBError",
            }
            if data_fault:
                return failure
            unavailable = failure
    return unavailable
