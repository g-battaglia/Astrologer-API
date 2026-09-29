"""Single patchable wall-clock source for current-moment endpoints."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the host's timezone-aware UTC time without external HTTP calls."""
    return datetime.now(timezone.utc)
