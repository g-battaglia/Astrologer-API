"""Uniform MCP tool-error handling and internal-detail sanitization."""

from __future__ import annotations

import json
import logging
from typing import Any

from kerykeion.schemas import KerykeionException
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError as PydanticValidationError

from ..utils.heavy_work import ServerBusyError


_INTERNAL_MESSAGE = "Internal server error. The failure has been logged."


def _public_error(exc: BaseException) -> dict[str, str]:
    """Map expected caller errors, hiding all unexpected exception text."""
    if isinstance(exc, (KerykeionException, PydanticValidationError, ValueError)):
        return {
            "status": "ERROR",
            "message": str(exc).strip() or type(exc).__name__,
            "error_type": type(exc).__name__,
        }
    if isinstance(exc, ServerBusyError):
        return {
            "status": "ERROR",
            "message": "Calculation capacity is currently busy. Retry after a short delay.",
            "error_type": "ServerBusy",
        }
    if isinstance(exc, TimeoutError):
        return {
            "status": "ERROR",
            "message": "The calculation exceeded its time budget.",
            "error_type": "TimeoutError",
        }
    return {
        "status": "ERROR",
        "message": _INTERNAL_MESSAGE,
        "error_type": "InternalServerError",
    }


def _raise_tool_error(payload: dict[str, Any]) -> None:
    """Raise a serialized envelope so the MCP transport sets ``isError=true``."""
    raise ToolError(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def install_mcp_error_boundary(mcp: Any) -> None:
    """Mark ERROR envelopes as failures only on the protocol transport.

    Direct ``mcp.call_tool`` remains a useful in-process API and preserves its
    historical ERROR dictionaries. The low-level request handler is what must
    convert those dictionaries to ``isError=true`` for remote clients.
    """
    logger = logging.getLogger("app.mcp.tools")
    original_call_tool = mcp.call_tool

    async def protocol_call_tool(name: str, arguments: dict[str, Any]):
        try:
            result = await original_call_tool(name, arguments)
        except ToolError as exc:
            # FastMCP wraps the callable's exception in ToolError. Classify the
            # original cause, not the wrapper text (which may contain paths or
            # request values), and serialize a fresh safe envelope.
            cause = exc.__cause__ or exc
            logger.error("%s failed | exception=%s", name, type(cause).__name__)
            _raise_tool_error(_public_error(cause))
        except Exception as exc:
            logger.error("%s failed | exception=%s", name, type(exc).__name__)
            _raise_tool_error(_public_error(exc))

        structured = result[1] if isinstance(result, tuple) and len(result) == 2 else None
        if isinstance(structured, dict) and structured.get("status") == "ERROR":
            _raise_tool_error(structured)
        return result

    mcp._mcp_server.call_tool(validate_input=False)(protocol_call_tool)
