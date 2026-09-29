"""MCP (Model Context Protocol) server for the Astrologer API v6.

Served via Streamable HTTP transport at /api/v6/mcp.
"""

from .server import mcp

__all__ = ["mcp"]
