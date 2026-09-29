"""Privacy-preserving logging helpers for HTTP requests."""

from __future__ import annotations

from logging import Logger
from uuid import uuid4

from fastapi import Request


def get_request_id(request: Request) -> str:
    """Return a server-generated identifier stable for this request.

    Client-provided identifiers are deliberately not trusted or logged: an
    arbitrary header can itself contain personal data or log-forging content.
    """
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = uuid4().hex
        request.state.request_id = request_id
    return request_id


def log_request(logger: Logger, request: Request, description: str) -> None:
    """Log only routing metadata, never network identity or request content."""
    logger.info(
        "%s %s | request_id=%s | %s",
        request.method,
        request.url.path,
        get_request_id(request),
        description,
    )


def log_request_with_body(logger: Logger, request: Request, description: str, body_json: str) -> None:
    """Compatibility wrapper that intentionally discards ``body_json``.

    Birth data, coordinates, names and GeoNames usernames are personal data.
    Keeping the old call signature lets every route use one privacy boundary
    without serialising those values into logs at any level.
    """
    del body_json
    log_request(logger, request, description)


def log_exception(logger: Logger, request: Request, operation: str, exc: BaseException) -> None:
    """Record a diagnosable error without logging its potentially sensitive text.

    Exception messages frequently interpolate request values. We therefore log
    only the exception class and the request correlation identifier. Tracebacks
    are intentionally omitted because their final line repeats the message.
    """
    logger.error(
        "%s failed | request_id=%s | path=%s | exception=%s",
        operation,
        get_request_id(request),
        request.url.path,
        type(exc).__name__,
    )
