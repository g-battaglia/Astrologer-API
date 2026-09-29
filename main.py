"""
This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import asyncio
import logging
import logging.config
import os
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import cast

import anyio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from .routers import (
    misc, charts, data, context, moon_phase, astro_calendar, fixed_stars,
    fixed_star_discovery, sun_times, moon_voc, dominants, returns, predictive,
    events, transits, ephemeris, analysis, traditional, locational, reports,
)
from .routers.legacy import register_legacy_v6_routes
from .config.settings import settings
from .mcp.server import create_mcp_server, mcp as default_mcp_server
from .middleware.secret_key_checker_middleware import SecretKeyCheckerMiddleware, auth_is_open
from .middleware.ephemeris_debug_middleware import EphemerisDebugMiddleware
from .middleware.ephemeris_readiness_middleware import EphemerisReadinessMiddleware
from .utils.cache_release import cache_release_loop
from .utils.ephemeris_readiness import is_ephemeris_ready
from .types.response_models import Public422Response
from .utils.logging_utils import log_exception
from .utils.validation_helpers import format_extra_field_error


logging.config.dictConfig(settings.LOGGING_CONFIG)

# Log dependency versions and ephemeris backend at startup
_logger = logging.getLogger(__name__)
try:
    from importlib.metadata import version as _pkg_version
    from kerykeion.ephemeris_backend import BACKEND_NAME as _backend

    _logger.info("kerykeion %s (backend=%s)", _pkg_version("kerykeion"), _backend)

    if _backend == "libephemeris":
        import libephemeris as _eph

        _mode = _eph.get_calc_mode()
        _tier = _eph.get_precision_tier()
        _network = _eph.get_network_policy()
        _parts = [f"mode={_mode}", f"tier={_tier}", f"network={_network}"]
        _logger.info("libephemeris %s (%s)", _eph.__version__, ", ".join(_parts))
except Exception:
    _logger.warning("ephemeris backend: detection failed")


# Pre-warm polling. Marker-absent polls cost one stat(), so a short interval is
# cheap; the deadline stops an unprovisionable worker from polling forever.
_PREWARM_POLL_INTERVAL_S = 2.0
_PREWARM_MAX_WAIT_S = 900.0


def _prewarm_enabled() -> bool:
    return os.environ.get("EPHEMERIS_PREWARM", "true").lower() not in ("0", "false", "no")


def _warm_ephemeris_readers() -> None:
    """Open, warm and then release the sealed readers. Blocking — thread only.

    Cooling an unvalidated reader would violate the startup boundary, so this
    only ever runs once the manifest-backed readiness gate has passed.
    """
    from kerykeion import AstrologicalSubjectFactory

    AstrologicalSubjectFactory.from_birth_data(
        name="warmup",
        year=2000,
        month=1,
        day=1,
        hour=0,
        minute=0,
        city="Greenwich",
        nation="GB",
        lng=0.0,
        lat=51.48,
        tz_str="Etc/UTC",
        online=False,
        suppress_geonames_warning=True,
    )
    try:
        import libephemeris as _eph

        reader = _eph.get_leb_reader()
        if reader:
            reader.cool()
        _eph.release_data_cache()
        _logger.info("Ephemeris page cache released")
    except Exception:
        pass


async def _prewarm_when_ready() -> None:
    """Wait for provisioning and prepare readers outside request handling.

    The marker may appear after HTTP startup. Polling validates and warms the
    data in a worker thread without blocking the event loop. Without a managed
    data directory, readiness proceeds directly to warm-up.
    """
    try:
        deadline = time.monotonic() + _PREWARM_MAX_WAIT_S
        while True:
            # Cheap until the marker lands (a bare stat); the single expensive
            # validation then runs here, in a thread — never on the event loop
            # and never inside a request holding _cache_lock.
            if await anyio.to_thread.run_sync(is_ephemeris_ready):
                break
            if time.monotonic() >= deadline:
                _logger.warning(
                    "Ephemeris pre-warm abandoned: runtime inventory still unvalidated after %.0fs; "
                    "the first request will warm the cache",
                    _PREWARM_MAX_WAIT_S,
                )
                return
            await asyncio.sleep(_PREWARM_POLL_INTERVAL_S)

        t0 = time.perf_counter()
        await anyio.to_thread.run_sync(_warm_ephemeris_readers)
        _logger.info("Ephemeris pre-warm complete (%.0f ms)", (time.perf_counter() - t0) * 1000)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        # A pre-warm failure is never fatal: the readiness gate still governs
        # calculation traffic and the first request re-does this work.
        _logger.warning("Ephemeris pre-warm failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the sealed runtime and own this app's MCP session manager."""
    prewarm_task: asyncio.Task | None = None
    cache_stop = asyncio.Event()
    cache_task = asyncio.create_task(cache_release_loop(cache_stop))
    if _prewarm_enabled():
        prewarm_task = asyncio.create_task(_prewarm_when_ready())
    else:
        _logger.info("Ephemeris pre-warm skipped (EPHEMERIS_PREWARM=false)")
    try:
        mcp_server = app.state.mcp_server
        async with mcp_server.session_manager.run():
            yield
    finally:
        # A pre-warm still polling or hashing at shutdown is abandoned here, so
        # it can never outlive the app or block a restart.
        if prewarm_task is not None:
            prewarm_task.cancel()
            with suppress(asyncio.CancelledError):
                await prewarm_task
        cache_stop.set()
        with suppress(asyncio.CancelledError):
            await cache_task
        # The heavy pool is deliberately NOT shut down here: it is module-level
        # state shared across lifespan cycles, so shutting it down would break
        # any process that starts the app twice (sequential TestClient context
        # managers, in-process restarts) with "cannot schedule new futures after
        # shutdown". Its non-daemon workers are joined at interpreter exit.


def generate_operation_id(route: APIRoute) -> str:
    """Derive a readable, stable operationId from the route path.

    FastAPI's default mangles the function name together with the whole path
    and the verb — ``transit_batch_data_api_v6_chart_data_transit_batch_post``.
    That string is not an internal detail: RapidAPI shows the operationId as
    the endpoint's NAME in its UI, and SDK generators turn it into a method
    name. The path alone already identifies the operation uniquely, so this
    builds camelCase from it: ``chartDataTransitBatch``.

    Stability matters more than beauty here — the id is a public identifier
    that SDK users call, so it is derived only from the URL, which changing
    would be a breaking change anyway.
    """
    segments = [segment for segment in route.path.split("/") if segment and segment not in ("api", "v6")]
    words: list[str] = []
    for segment in segments:
        # Path params ({planet}) describe the same operation; the literal
        # segments already disambiguate it.
        if segment.startswith("{"):
            continue
        words.extend(part for part in segment.replace("-", "_").split("_") if part)

    if not words:
        return route.name

    head, *tail = words
    return head.lower() + "".join(word.capitalize() for word in tail)


# ------------------------------------------------------------------------------
# OpenAPI metadata: tag descriptions and the error responses every calculation
# route can actually emit (kept in sync with app/utils/router_utils.handle_exception
# and the auth/readiness middleware).
# ------------------------------------------------------------------------------

OPENAPI_TAGS = [
    {"name": "Charts", "description": "Rendered SVG wheels plus the full chart data: natal, synastry, composite, transit, solar and lunar returns, and the current sky."},
    {"name": "Chart Data", "description": "The same calculations as Charts, JSON only (no SVG rendering): subjects, chart data, transit batches and the compatibility score."},
    {"name": "AI Context", "description": "Chart data plus an AI-optimized prose `context` string, ready to feed to a language model."},
    {"name": "Moon Phase", "description": "Moon phase details for a moment and location, with `now-utc` variants and AI context."},
    {"name": "Sun & Planetary Hours", "description": "Sunrise, sunset, twilights and the 24 Chaldean planetary hours for a civil date and location."},
    {"name": "Void of Course Moon", "description": "Void-of-course state at a moment and VoC windows over a date range."},
    {"name": "Dominants", "description": "Chart dominants: planet, sign, element, modality and house, with selectable strategy."},
    {"name": "Returns", "description": "Heliocentric and lunar-node-crossing returns, available as charts, data and context."},
    {"name": "Predictive", "description": "Progressions, solar arc directions and primary directions."},
    {"name": "Events", "description": "Astronomical events and bounded searches."},
    {"name": "Transits", "description": "Transit batches, timelines and daily aspects."},
    {"name": "Ephemeris", "description": "Bounded ephemeris tables."},
    {"name": "Analysis", "description": "Midpoints, declinations and planetary-node analysis."},
    {"name": "Traditional", "description": "Time lords and horary indicators."},
    {"name": "Locational", "description": "Relocated charts and astro-cartography."},
    {"name": "Reports", "description": "Text reports from astrological calculations."},
    {"name": "Astro Calendar", "description": "A month-grid aggregator: ingresses, lunations, eclipses, stations, VoC windows, aspectarian, sign and retrograde periods."},
    {"name": "Fixed Stars", "description": "The fixed-star catalog usable with `subject.active_fixed_stars`."},
]

_ERROR_EXAMPLE = {"status": "ERROR", "message": "..."}
CALCULATION_ERROR_RESPONSES: dict = {
    400: {
        "description": "Typed calculation error (`error_type`: `DstTransitionError`, `DateRangeError`, `GeoNamesLookupError`, or a kerykeion domain error). Fix the input; do not retry unchanged.",
        "content": {"application/json": {"example": {"status": "ERROR", "message": "Ambiguous local time.", "error_type": "DstTransitionError"}}},
    },
    403: {
        "description": "Missing or invalid API secret header.",
        "content": {"application/json": {"example": {"status": "KO", "message": "Forbidden: Invalid or missing secret key"}}},
    },
    500: {
        "description": "Unexpected server error (sanitized).",
        "content": {"application/json": {"example": {"status": "ERROR", "message": "Internal server error. The failure has been logged.", "error_type": "InternalServerError"}}},
    },
    502: {
        "description": "Upstream GeoNames lookup unreachable (only when resolving a city via `geonames_username`).",
        "content": {"application/json": {"example": _ERROR_EXAMPLE}},
    },
    503: {
        "description": "Sealed ephemeris runtime still provisioning (`error_type`: `ServiceInitializing`, `Retry-After: 60`) or a feature unsupported by the deployment.",
        "content": {"application/json": {"example": {"status": "ERROR", "message": "Service initializing", "error_type": "ServiceInitializing"}}},
    },
    504: {
        "description": "A long search exceeded its time budget; reduce the span, `count` or resolution and retry.",
        "content": {"application/json": {"example": _ERROR_EXAMPLE}},
    },
}
CALCULATION_ERROR_RESPONSES[422] = {
    "description": "Request validation or a typed capability/resource refusal.",
    "model": Public422Response,
}
READONLY_ERROR_RESPONSES: dict = {k: CALCULATION_ERROR_RESPONSES[k] for k in (403, 500, 503)}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors that provides helpful suggestions
    when users send incorrect field names.
    """
    enriched_errors = []

    for error in exc.errors():
        error_type = error.get("type", "")

        # Check if this is an "extra fields not permitted" error
        if error_type == "extra_forbidden":
            # Get the field name from the location
            location = error.get("loc", [])
            if location:
                field_name = str(location[-1])
                enriched_message = format_extra_field_error(field_name, list(location))
                enriched_errors.append(
                    {
                        "loc": location,
                        "msg": enriched_message,
                        "type": error_type,
                    }
                )
                continue

        # Enrich "missing" errors with a readable field path
        if error_type == "missing":
            location = error.get("loc", [])
            parts = [str(loc) for loc in location if loc != "body"]
            if len(parts) >= 2:
                field_name = parts[-1]
                parent_path = ".".join(parts[:-1])
                msg = f"Field required: '{field_name}' is missing in '{parent_path}'."
            elif len(parts) == 1:
                msg = f"Field required: '{parts[0]}' is missing."
            else:
                msg = error.get("msg", "Field required")
            enriched_errors.append({"loc": location, "msg": msg, "type": error_type})
            continue

        # For other errors, sanitize the error to be JSON serializable
        # Remove 'ctx' which may contain non-serializable objects like ValueError
        sanitized_error = {
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error_type,
        }
        enriched_errors.append(sanitized_error)

    logging.warning(
        "Validation error | request_id=%s | path=%s | issue_count=%d | issue_types=%s",
        request.state.request_id if hasattr(request.state, "request_id") else "unassigned",
        request.url.path,
        len(enriched_errors),
        sorted({str(error.get("type", "unknown")) for error in enriched_errors}),
    )

    return JSONResponse(
        status_code=422,
        content={
            "status": "ERROR",
            "message": "Validation failed",
            "errors": enriched_errors,
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    log_exception(_logger, request, "unhandled request", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "ERROR", "message": "Internal Server Error"},
    )


async def deprecated_mcp_sse(request: Request) -> Response:
    """Retire the stateful legacy transport without redirecting protocols."""
    return JSONResponse(
        status_code=410,
        content={
            "status": "ERROR",
            "message": "The legacy MCP SSE transport has been retired. Use Streamable HTTP at /api/v6/mcp/.",
            "error_type": "TransportRetired",
        },
    )


def _install_openapi_security(application: FastAPI) -> None:
    base_openapi = application.openapi

    def openapi_with_security():
        schema = base_openapi()
        names = settings.secret_key_names
        if isinstance(names, str):
            names = [names] if names else []
        if names:
            schemes = {name.replace("-", ""): {"type": "apiKey", "name": name, "in": "header"} for name in names}
            schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(schemes)
            security = [{key: []} for key in schemes]
            public_paths = {"/health", "/ready"}
            for path, path_item in schema.get("paths", {}).items():
                for operation in path_item.values():
                    if isinstance(operation, dict) and "responses" in operation:
                        operation["security"] = [] if path in public_paths else security
        return schema

    application.openapi = openapi_with_security  # type: ignore[method-assign]


def create_app(mcp_server=None) -> FastAPI:
    """Create an independent application and MCP lifecycle."""
    if mcp_server is None:
        mcp_server = create_mcp_server()

    application = FastAPI(
        debug=settings.debug,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        generate_unique_id_function=generate_operation_id,
        title="Astrologer API",
        version="6.0.0",
        summary="Data Driven Astrology",
        description=(
            "The Astrologer API is a RESTful service providing extensive astrology calculations, designed for seamless "
            "integration into projects. It offers a rich set of astrological charts and data, making it an invaluable tool "
            "for both developers and astrology enthusiasts.\n\n"
            "All calculation routes live under `/api/v6` and are POST unless noted; requests authenticate with an API secret "
            "header (see the security schemes). A stateless Model Context Protocol server is mounted at `/api/v6/mcp/` "
            "(Streamable HTTP). `GET /health` and `GET /ready` are unauthenticated liveness/readiness probes."
        ),
        openapi_tags=OPENAPI_TAGS,
        contact={
            "name": "Kerykeion Astrology",
            "url": "https://www.kerykeion.net/",
            "email": settings.admin_email,
        },
        license_info={
            "name": "AGPL-3.0",
            "url": "https://www.gnu.org/licenses/agpl-3.0.html",
        },
        lifespan=lifespan,
    )
    application.state.mcp_server = mcp_server

    application.include_router(charts.router, tags=["Charts"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(data.router, tags=["Chart Data"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(context.router, tags=["AI Context"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(moon_phase.router, tags=["Moon Phase"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(sun_times.router, tags=["Sun & Planetary Hours"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(moon_voc.router, tags=["Void of Course Moon"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(dominants.router, tags=["Dominants"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(returns.router, tags=["Returns"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(predictive.router, tags=["Predictive"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(events.router, tags=["Events"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(transits.router, tags=["Transits"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(ephemeris.router, tags=["Ephemeris"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(analysis.router, tags=["Analysis"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(traditional.router, tags=["Traditional"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(locational.router, tags=["Locational"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(reports.router, tags=["Reports"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(astro_calendar.router, tags=["Astro Calendar"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(fixed_stars.router, tags=["Fixed Stars"], responses=READONLY_ERROR_RESPONSES)
    application.include_router(fixed_star_discovery.router, tags=["Fixed Stars"], responses=CALCULATION_ERROR_RESPONSES)
    application.include_router(misc.router, tags=["Miscellaneous"])

    register_legacy_v6_routes(application)

    # Mounted directly: FastAPI routers do not propagate Starlette Mounts.
    application.mount("/api/v6/mcp", mcp_server.streamable_http_app())
    application.add_route("/api/v6/mcp-sse", deprecated_mcp_sse, methods=["GET", "POST"])
    application.add_route("/api/v6/mcp-sse/{legacy_path:path}", deprecated_mcp_sse, methods=["GET", "POST"])

    application.add_exception_handler(
        RequestValidationError,
        cast(Callable[[Request, Exception], Response | Awaitable[Response]], validation_exception_handler),
    )
    application.add_exception_handler(Exception, global_exception_handler)
    _install_openapi_security(application)

    # Added first = innermost, so authentication still precedes readiness.
    application.add_middleware(EphemerisReadinessMiddleware)

    if not settings.debug:
        configured_secret_keys = [
            key
            for key in (
                settings.rapid_api_secret_key,
                settings.astrologer_studio_secret_key,
                settings.private_astrologer_api_secret_key,
                settings.rapid_api_key,
            )
            if key
        ]
        allow_no_auth = os.environ.get("ASTROLOGER_ALLOW_NO_AUTH", "").lower() in ("1", "true", "yes")
        if auth_is_open(settings.secret_key_names, configured_secret_keys) and not allow_no_auth:
            raise RuntimeError(
                "Authentication is not configured while debug=false: secret key values "
                "(rapid_api_secret_key / astrologer_studio_secret_key / private_astrologer_api_secret_key / "
                "rapid_api_key) and/or secret_key_names are empty, which would let the middleware pass every "
                "request through. Refusing to start an unauthenticated production API. "
                "Set ASTROLOGER_ALLOW_NO_AUTH=true to override for local testing."
            )
        application.add_middleware(
            SecretKeyCheckerMiddleware,
            secret_key_names=settings.secret_key_names,
            secret_keys=configured_secret_keys,
        )

    if settings.enable_tracing:
        application.add_middleware(EphemerisDebugMiddleware)

    _logger.warning(
        "CORS posture: allow_origins='*' with allow_credentials=True (open by design); allowed_cors_origins=%r and allowed_hosts (%d entries) from config are not enforced.",
        settings.allowed_cors_origins,
        len(settings.allowed_hosts),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return application


# Production ASGI entrypoint and backwards-compatible global test surface.
app = create_app(default_mcp_server)
