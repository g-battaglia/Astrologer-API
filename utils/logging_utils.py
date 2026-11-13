"""Privacy-preserving request events, complementary to edge access logs."""

from __future__ import annotations

import logging
from logging import Logger
import re
from uuid import uuid4

from fastapi import Request

from .observability import emit, request_fields


def get_request_id(request: Request) -> str:
    """Keep only server-generated identifiers; never inspect inbound headers."""
    request_id = getattr(request.state, "request_id", None)
    if type(request_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", request_id):
        request_id = uuid4().hex
        request.state.request_id = request_id
    return request_id


def log_request(logger: Logger, request: Request, description: str) -> None:
    """Keep normal accept events debug-only: edge logs already count requests."""
    del description
    emit(logger, "api.request", level=logging.DEBUG, request_id=get_request_id(request), **request_fields(request))


def log_request_with_body(logger: Logger, request: Request, description: str, body_json: str) -> None:
    """Compatibility signature: neither body nor prose reaches any sink."""
    del body_json
    log_request(logger, request, description)


def log_exception(logger: Logger, request: Request, operation: str, exc: BaseException) -> None:
    """Classify by known types, not potentially sensitive exception messages."""
    del operation
    kind = type(exc)
    known: dict[type[BaseException], str] = {
        RuntimeError: "RuntimeError",
        TypeError: "TypeError",
        ValueError: "ValueError",
        TimeoutError: "TimeoutError",
        MemoryError: "MemoryError",
        OSError: "OSError",
    }
    fault = "timeout" if kind is TimeoutError else "resource" if kind is MemoryError else "internal"
    emit(
        logger,
        "api.exception",
        level=logging.ERROR,
        request_id=get_request_id(request),
        exception_type=known.get(kind, "Exception"),
        fault=fault,
        outcome="unavailable",
        availability_impact="unavailable",
        **request_fields(request),
    )
