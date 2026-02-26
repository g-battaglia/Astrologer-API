"""
Moon phase endpoints - detailed lunar phase data.

Endpoints under /api/v5/moon-phase/*.
"""

from datetime import datetime, timezone
from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory

from ..types.request_models import MoonPhaseRequestModel, NowMoonPhaseRequestModel
from ..types.response_models import (
    MoonPhaseContextResponseModel,
    MoonPhaseResponseModel,
)
from ..utils.get_time_from_google import get_time_from_google
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import (
    create_moon_phase_overview,
    handle_exception,
    moon_phase_context_payload,
    moon_phase_payload,
    resolve_active_points,
)

logger = getLogger(__name__)

router = APIRouter()


@router.post("/api/v5/moon-phase", response_model=MoonPhaseResponseModel)
async def moon_phase(
    request_body: MoonPhaseRequestModel, request: Request
) -> JSONResponse:
    """
    **POST** `/api/v5/moon-phase`

    Returns detailed moon phase information for a specific date/time and location.

    Includes: phase name, illumination, stage (waxing/waning), age, upcoming major phases,
    next lunar/solar eclipses, sunrise/sunset, sun position, and zodiac signs.

    **Parameters:**
    - `year`, `month`, `day`, `hour`, `minute`: Date and time of the event (required).
    - `second`: Seconds (optional, default 0).
    - `latitude`, `longitude`, `timezone`: Geographic location (required).
    - `using_default_location`: Metadata flag (optional, default false).
    - `location_precision`: Decimal precision for coordinates in response (optional, default 0).

    **Returns:**
    - `status`: "OK"
    - `moon_phase_overview`: MoonPhaseOverviewModel
    """
    log_request_with_body(
        logger, request, "Moon phase request", request_body.model_dump_json()
    )

    try:
        overview = create_moon_phase_overview(request_body)
        return JSONResponse(content=moon_phase_payload(overview), status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/moon-phase/context", response_model=MoonPhaseContextResponseModel)
async def moon_phase_context(
    request_body: MoonPhaseRequestModel, request: Request
) -> JSONResponse:
    """
    **POST** `/api/v5/moon-phase/context`

    Returns detailed moon phase information with AI-optimized XML context.

    **Parameters:**
    - `year`, `month`, `day`, `hour`, `minute`: Date and time of the event (required).
    - `second`: Seconds (optional, default 0).
    - `latitude`, `longitude`, `timezone`: Geographic location (required).
    - `using_default_location`: Metadata flag (optional, default false).
    - `location_precision`: Decimal precision for coordinates in response (optional, default 0).

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized XML context string
    - `moon_phase_overview`: MoonPhaseOverviewModel
    """
    log_request_with_body(
        logger, request, "Moon phase context request", request_body.model_dump_json()
    )

    try:
        overview = create_moon_phase_overview(request_body)
        return JSONResponse(
            content=moon_phase_context_payload(overview), status_code=200
        )
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/moon-phase/now-utc", response_model=MoonPhaseResponseModel)
async def moon_phase_now_utc(
    request_body: NowMoonPhaseRequestModel, request: Request
) -> JSONResponse:
    """
    **POST** `/api/v5/moon-phase/now-utc`

    Returns detailed moon phase information for the current UTC moment at Greenwich.

    Uses the current UTC time and Greenwich Observatory coordinates (51.4779 N, 0.0015 W).

    **Parameters:**
    - `using_default_location`: Metadata flag (optional, default true).
    - `location_precision`: Decimal precision for coordinates in response (optional, default 0).

    **Returns:**
    - `status`: "OK"
    - `moon_phase_overview`: MoonPhaseOverviewModel
    """
    log_request_with_body(
        logger, request, "Moon phase now-utc request", request_body.model_dump_json()
    )

    try:
        try:
            utc_datetime = get_time_from_google()
        except Exception as time_exc:  # pragma: no cover - fallback path
            logger.warning("Falling back to system UTC time: %s", time_exc)
            utc_datetime = datetime.now(timezone.utc)

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Moon Phase",
            year=utc_datetime.year,  # type: ignore[arg-type]
            month=utc_datetime.month,  # type: ignore[arg-type]
            day=utc_datetime.day,  # type: ignore[arg-type]
            hour=utc_datetime.hour,  # type: ignore[arg-type]
            minute=utc_datetime.minute,  # type: ignore[arg-type]
            seconds=utc_datetime.second,  # type: ignore[arg-type]
            city="Greenwich",
            nation="GB",
            lng=-0.001545,
            lat=51.477928,
            tz_str="Etc/UTC",
            online=False,
            active_points=resolve_active_points(None),
            suppress_geonames_warning=True,
        )

        overview = MoonPhaseDetailsFactory.from_subject(
            subject,
            using_default_location=request_body.using_default_location,
            location_precision=request_body.location_precision,
        )

        return JSONResponse(content=moon_phase_payload(overview), status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post(
    "/api/v5/moon-phase/now-utc/context", response_model=MoonPhaseContextResponseModel
)
async def moon_phase_now_utc_context(
    request_body: NowMoonPhaseRequestModel, request: Request
) -> JSONResponse:
    """
    **POST** `/api/v5/moon-phase/now-utc/context`

    Returns detailed moon phase information for the current UTC moment at Greenwich
    with AI-optimized XML context.

    **Parameters:**
    - `using_default_location`: Metadata flag (optional, default true).
    - `location_precision`: Decimal precision for coordinates in response (optional, default 0).

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized XML context string
    - `moon_phase_overview`: MoonPhaseOverviewModel
    """
    log_request_with_body(
        logger,
        request,
        "Moon phase now-utc context request",
        request_body.model_dump_json(),
    )

    try:
        try:
            utc_datetime = get_time_from_google()
        except Exception as time_exc:  # pragma: no cover - fallback path
            logger.warning("Falling back to system UTC time: %s", time_exc)
            utc_datetime = datetime.now(timezone.utc)

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Moon Phase",
            year=utc_datetime.year,  # type: ignore[arg-type]
            month=utc_datetime.month,  # type: ignore[arg-type]
            day=utc_datetime.day,  # type: ignore[arg-type]
            hour=utc_datetime.hour,  # type: ignore[arg-type]
            minute=utc_datetime.minute,  # type: ignore[arg-type]
            seconds=utc_datetime.second,  # type: ignore[arg-type]
            city="Greenwich",
            nation="GB",
            lng=-0.001545,
            lat=51.477928,
            tz_str="Etc/UTC",
            online=False,
            active_points=resolve_active_points(None),
            suppress_geonames_warning=True,
        )

        overview = MoonPhaseDetailsFactory.from_subject(
            subject,
            using_default_location=request_body.using_default_location,
            location_precision=request_body.location_precision,
        )

        return JSONResponse(
            content=moon_phase_context_payload(overview), status_code=200
        )

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
