"""FastMCP server factory for the Astrologer API v6.

Every FastAPI application receives its own FastMCP instance and one-shot session
manager. Streamable HTTP is stateless, so requests remain valid when Uvicorn
routes consecutive calls to different worker processes.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings


def create_mcp_server() -> FastMCP:
    """Build and register an independent Astrologer MCP server."""
    server = FastMCP(
        "Astrologer",
        instructions=(
            "Astrological calculations powered by Kerykeion v6. "
            "Use get_birth_chart for natal charts, get_synastry for relationship analysis, "
            "get_transit for current planetary influences, and get_moon_phase for lunar data. "
            "All chart tools support include_ai_context (default True) for LLM-optimized output. "
            "Read the resources (astrologer://docs/*) for reference documentation."
        ),
        streamable_http_path="/",
        stateless_http=True,
        # This transport is mounted inside FastAPI and served publicly (reverse proxy /
        # RapidAPI domains), not on FastMCP's own localhost server. DNS-rebinding
        # protection is for localhost MCP servers; FastAPI auth protects this host.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    # Imports stay local so constructing a test app cannot observe a partially
    # initialized module-level server.
    from app.mcp.error_boundary import install_mcp_error_boundary
    from app.mcp.resources import register_resources
    from app.mcp.tools.advanced_tools import register_advanced_tools
    from app.mcp.tools.core_tools import register_core_tools
    from app.mcp.tools.moon_phase_tools import register_moon_phase_tools

    register_core_tools(server)
    register_moon_phase_tools(server)
    register_advanced_tools(server)
    register_resources(server)
    install_mcp_error_boundary(server)
    return server


# Backwards-compatible direct-call surface used by internal tests and scripts.
# The production FastAPI app explicitly adopts this instance; create_app() uses
# a fresh one unless a caller supplies an instance.
mcp = create_mcp_server()
