"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

ENFORCE_DOMAIN_WILDCARD = "Domain wildcard patterns must be like '*.example.com'."


class RapidApiMiddleware:
    def __init__(self, app: ASGIApp, secret_keys: list = [], www_redirect: bool = True) -> None:
        self.app = app
        self.allowed_hosts = list(secret_keys)
        self.www_redirect = www_redirect

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        headers = Headers(scope=scope)
        host = headers.get("X-RapidAPI-Proxy-Secret", "").split(":")[0]
        is_valid_key = False
        found_www_redirect = False

        for key in self.allowed_hosts:
            if host == key:
                is_valid_key = True
                break

        if is_valid_key:
            await self.app(scope, receive, send)

        else:
            response: Response

            if found_www_redirect and self.www_redirect:
                url = URL(scope=scope)
                redirect_url = url.replace(netloc="www." + url.netloc)
                response = RedirectResponse(url=str(redirect_url))

            else:
                response = JSONResponse(status_code=400, content={"status": "KO", "message": "Bad request"})

            await response(scope, receive, send)
