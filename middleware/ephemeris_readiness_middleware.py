"""Manifest-backed ephemeris readiness gate — raw ASGI.

Calculation workers run with sealed network access. Until the provisioner has
downloaded and checksum-validated every required artifact, published an atomic
marker, and the process has revalidated the active inventory, engine calls must
not begin.

Instead, answer ``/api/v6/*`` requests with an honest 503 + Retry-After
until the runtime is ready. ``/health``, ``/ready`` and ``/`` stay reachable so
operators can distinguish liveness from readiness and inspect the failure.
"""

import json
from typing import Any, Callable, Dict

import anyio

from ..utils.ephemeris_readiness import is_ephemeris_ready, is_ephemeris_ready_latched

_RETRY_AFTER_S = 60

_BODY = json.dumps(
    {
        "status": "ERROR",
        "message": (f"The sealed ephemeris runtime is not ready; provisioning or inventory validation is still pending. Retry in about {_RETRY_AFTER_S} seconds."),
        "error_type": "ServiceInitializing",
    }
).encode("utf-8")


class EphemerisReadinessMiddleware:
    """Return 503 for calculation routes until the runtime contract passes."""

    __slots__ = ("app",)

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        runtime_ready = True
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/v6"):
            # Steady state: once a positive validation is latched the gate is a
            # synchronous flag read — no thread dispatch, no stat per request.
            # Until then, the post-marker validation opens and authenticates
            # the LEB inventory, so keep that disk work off the event loop;
            # the short negative TTL in get_ephemeris_status() bounds how
            # often a failing runtime is revalidated.
            runtime_ready = is_ephemeris_ready_latched() or await anyio.to_thread.run_sync(is_ephemeris_ready)
        if not runtime_ready:
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(_BODY)).encode()),
                        (b"retry-after", str(_RETRY_AFTER_S).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": _BODY})
            return
        await self.app(scope, receive, send)
