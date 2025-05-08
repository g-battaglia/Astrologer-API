"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import logging

class SecretKeyCheckerMiddleware:
    def __init__(self, app: ASGIApp, secret_key_name: str, secret_keys: list = []) -> None:
        self.app = app
        self.secret_key_values = list(secret_keys)
        self.secret_key_name = secret_key_name

        if not self.secret_key_name or not self.secret_key_values:
            logging.critical("Secret key name or secret key values not set. The middleware will let all requests pass through!")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        headers = Headers(scope=scope)
        header_key = headers.get(self.secret_key_name, "").split(":")[0]
        is_valid_key = False

        for key in self.secret_key_values:
            if header_key == key:
                is_valid_key = True
                break

        if is_valid_key:
            await self.app(scope, receive, send)

        else:
            response = JSONResponse(status_code=400, content={"status": "KO", "message": "Bad request"})

            await response(scope, receive, send)
