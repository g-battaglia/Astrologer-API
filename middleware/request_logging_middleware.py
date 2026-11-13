"""Log the response status and retain the request body only for failures."""

import logging

import anyio
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..utils.logging_utils import get_request_id
from ..utils.observability import emit, request_fields

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or path.startswith(("/api/v6/mcp/", "/api/v6/mcp-sse")) or path == "/api/v6/mcp":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        chunks: list[bytes] = []
        complete = False
        disconnected = False

        async def capture() -> Message:
            nonlocal complete, disconnected
            message = await receive()
            if message["type"] == "http.request":
                if message.get("body"):
                    chunks.append(message["body"])
                complete = not message.get("more_body", False)
            elif message["type"] == "http.disconnect":
                disconnected = True
            return message

        async def log_response(message: Message) -> None:
            if message["type"] == "http.response.start":
                status = message["status"]
                fields = request_fields(request)
                request_id = get_request_id(request)
                if status == 200:
                    emit(logger, "api.request.ok", request_id=request_id, http_status=status, **fields)
                else:
                    # Early responses can leave the input unread. Give an
                    # in-flight upload a bounded chance to finish.
                    with anyio.move_on_after(1):
                        while not complete and not disconnected:
                            await capture()
                    emit(
                        logger,
                        "api.request.failed",
                        level=logging.ERROR,
                        request_id=request_id,
                        http_status=status,
                        request_body=b"".join(chunks),
                        request_body_complete=complete,
                        **fields,
                    )
                chunks.clear()
            await send(message)

        await self.app(scope, capture, log_response)
