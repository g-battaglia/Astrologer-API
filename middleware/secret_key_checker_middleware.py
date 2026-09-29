"""
This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import hmac
import logging

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def normalize_secret_config(secret_key_names: str | list[str], secret_keys: list) -> tuple[list[str], list[str]]:
    """Normalize raw secret config into ``(names, values)`` with empties removed."""
    values = [key for key in secret_keys if key]
    if isinstance(secret_key_names, str):
        names = [secret_key_names] if secret_key_names else []
    else:
        names = [name for name in secret_key_names if name]
    return names, values


def auth_is_open(secret_key_names: str | list[str], secret_keys: list) -> bool:
    """True if this config would let *every* request through (no header names or
    no key values configured).

    Shared by the middleware (``pass_all``) and the app's fail-closed startup
    guard so the two can never disagree about what "unauthenticated" means.
    """
    names, values = normalize_secret_config(secret_key_names, secret_keys)
    return not names or not values


class SecretKeyCheckerMiddleware:
    # Paths excluded from authentication (public endpoints)
    EXCLUDED_PATHS: set[str] = {"/health", "/ready"}

    def __init__(self, app: ASGIApp, secret_key_names: str | list[str], secret_keys: list = []) -> None:
        self.app = app
        self.secret_key_names, self.secret_key_values = normalize_secret_config(secret_key_names, secret_keys)
        # Pre-encode the valid keys to bytes: hmac.compare_digest rejects
        # non-ASCII `str` inputs (TypeError), and header values arrive latin-1
        # decoded, so a header byte >= 0x80 would otherwise crash the request.
        self._secret_key_values_bytes = [key.encode("utf-8") for key in self.secret_key_values]
        self.pass_all = not self.secret_key_names or not self.secret_key_values

        if self.pass_all:
            logging.critical("Secret key name or secret key values not set. The middleware will let all requests pass through!")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self.pass_all:
            await self.app(scope, receive, send)
            return

        # Skip authentication for excluded paths (e.g., /health)
        path = scope.get("path", "")
        if path in self.EXCLUDED_PATHS:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)

        # OR logic: accept if at least one header contains a valid key.
        # hmac.compare_digest keeps the comparison constant-time; comparing on
        # bytes (not str) avoids the non-ASCII TypeError for hostile headers.
        for key_name in self.secret_key_names:
            header_value = headers.get(key_name, "").split(":")[0].encode("utf-8")
            if any(hmac.compare_digest(header_value, valid) for valid in self._secret_key_values_bytes):
                await self.app(scope, receive, send)
                return

        response = JSONResponse(
            status_code=403,
            content={
                "status": "KO",
                "message": "Forbidden: Invalid or missing secret key",
            },
        )
        await response(scope, receive, send)
