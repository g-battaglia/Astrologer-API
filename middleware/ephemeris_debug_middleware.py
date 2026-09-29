"""
Ephemeris debug middleware — opt-in ASGI middleware.

Activated exclusively by the ``X-Debug-Ephemeris: true`` request header.
When active, wraps chart computation in an :class:`EphemerisSourceCollector`
that uses libephemeris's ContextVar-based tracing to capture which
sub-backend (LEB, Skyfield, Horizons, SPK, ASSIST, Keplerian) computed
each celestial body, then injects an ``_ephemeris_debug`` key into the
JSON response body.

Registration is gated by the ``enable_tracing`` setting (default ``false``
in production, ``true`` in test/dev).

When the header is absent the middleware is a transparent pass-through with
zero measurable overhead (single ``dict`` lookup on raw ASGI headers).
"""

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from ..utils.ephemeris_source_collector import EphemerisSourceCollector

logger = logging.getLogger(__name__)

_HEADER_NAME = b"x-debug-ephemeris"
_HEADER_VALUE = b"true"


class EphemerisDebugMiddleware:
    """
    Raw ASGI middleware — zero overhead when the debug header is absent.

    When ``X-Debug-Ephemeris: true`` is present:

    1. Enters an :class:`EphemerisSourceCollector` context that activates
       libephemeris's ContextVar-based tracing accumulator.
    2. Buffers the JSON response body.
    3. Injects ``_ephemeris_debug`` with the captured backend map.
    4. Forwards the (possibly modified) response.
    """

    __slots__ = ("app",)

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Never buffer the MCP transports: their responses are long-lived
        # streams (SSE / streamable HTTP) and buffering would never complete.
        if scope.get("path", "").startswith("/api/v6/mcp"):
            await self.app(scope, receive, send)
            return

        # Fast path: check for debug header in raw ASGI headers.
        if not _has_debug_header(scope.get("headers", [])):
            await self.app(scope, receive, send)
            return

        # Slow path: capture ephemeris backend sources.
        await self._handle_debug_request(scope, receive, send)

    async def _handle_debug_request(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        collector = EphemerisSourceCollector()
        response_start: Dict[str, Any] | None = None
        body_parts: List[bytes] = []

        async def capture_send(message: Dict[str, Any]) -> None:
            nonlocal response_start
            if message["type"] == "http.response.start":
                response_start = message
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        with collector:
            await self.app(scope, receive, capture_send)

        # Assemble body
        raw_body = b"".join(body_parts)
        sources = collector.get_sources()

        # Only inject into JSON responses that yielded backend hits.
        if response_start and sources and _is_json(response_start):
            try:
                data = json.loads(raw_body)
                # Top-level arrays/scalars can't carry the debug key — pass
                # them through untouched instead of raising TypeError.
                if isinstance(data, dict):
                    data["_ephemeris_debug"] = {
                        "backends": sources,
                    }
                    raw_body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                    response_start["headers"] = _update_content_length(response_start.get("headers", []), len(raw_body))
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.debug("ephemeris debug: could not inject into response body")

        # Forward the (possibly modified) response.
        if response_start:
            await send(response_start)
        await send({"type": "http.response.body", "body": raw_body})


# ---------------------------------------------------------------------------
# Helpers (module-private)
# ---------------------------------------------------------------------------


def _has_debug_header(headers: List[Tuple[bytes, bytes]]) -> bool:
    """Check for ``X-Debug-Ephemeris: true`` in raw ASGI headers."""
    for name, value in headers:
        if name == _HEADER_NAME and value.strip().lower() == _HEADER_VALUE:
            return True
    return False


def _is_json(response_start: Dict[str, Any]) -> bool:
    """Return True when the response content-type is JSON."""
    for name, value in response_start.get("headers", []):
        if name == b"content-type":
            return b"application/json" in value
    return False


def _update_content_length(headers: List[Tuple[bytes, bytes]], new_length: int) -> List[Tuple[bytes, bytes]]:
    """Return a new header list with an updated ``content-length``."""
    return [(name, str(new_length).encode() if name == b"content-length" else value) for name, value in headers]
