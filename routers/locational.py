"""Locational API endpoints."""

from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import (
    AstroCartographyFactory,
    RelocatedChartFactory,
)
from ..types.request_models import (
    AstroCartographyRequestModel,
    RelocatedChartRequestModel,
)
from ..types.response_models import (
    AstroCartographyResponseModel,
    RelocatedChartResponseModel,
)
from ..utils.router_utils import (
    build_subject,
    dump,
    handle_exception,
    resolve_active_points,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/locational/relocated-chart", response_model=RelocatedChartResponseModel, operation_id="advancedRelocatedChart")
async def relocated_chart(request_body: RelocatedChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/locational/relocated-chart`

    Relocate a natal chart to a new geographic location.
    Preserves original planetary positions but recalculates houses and angles.

    **Parameters:**
    - `subject`: Original natal subject.
    - `new_latitude`, `new_longitude`: New location coordinates.
    - `new_city`, `new_nation`, `new_timezone`: Optional location metadata.
    - `active_points`: Optional list of points to calculate (defaults to the
      standard active set).

    **Returns:**
    - `subject`: Relocated astrological subject.
    """
    log_request_with_body(logger, request, "Relocated chart request", request_body.model_dump_json())

    try:
        subject = await run_heavy(
            build_subject,
            request_body.subject,
            active_points=resolve_active_points(request_body.active_points),
        )
        relocated = await run_heavy(
            RelocatedChartFactory.relocate,
            subject,
            new_lat=request_body.new_latitude,
            new_lng=request_body.new_longitude,
            new_city=request_body.new_city,
            new_nation=request_body.new_nation,
            new_tz_str=request_body.new_timezone,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "subject": dump(relocated),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/locational/astro-cartography", response_model=AstroCartographyResponseModel, operation_id="advancedAstroCartography")
async def astro_cartography(request_body: AstroCartographyRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/locational/astro-cartography`

    Compute astro-cartography (ACG) planetary lines showing where planets cross
    ASC/DSC/MC/IC lines on the Earth's surface.

    **Parameters:**
    - `subject`: Natal subject.
    - `step`: Longitude resolution in degrees (default 1.0).
    - `tolerance`: Altitude tolerance for line detection.
    - `lat_range_min`, `lat_range_max`: Latitude bounds (default -66 to 66).
    - `planets`: Optional list of planets to calculate.

    **Returns:**
    - `lines`: List of ACG lines with planet, type, and coordinate points.
    """
    log_request_with_body(logger, request, "Astro-cartography request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        kwargs = {
            "step": request_body.step,
            "lat_range": (request_body.lat_range_min, request_body.lat_range_max),
        }
        if request_body.tolerance is not None:
            kwargs["tolerance"] = request_body.tolerance
        if request_body.planets is not None:
            kwargs["planets"] = request_body.planets

        lines = await run_heavy(AstroCartographyFactory.compute, subject, **kwargs)

        return JSONResponse(
            content={
                "status": "OK",
                "lines": dump(lines),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
