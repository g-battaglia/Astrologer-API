"""
Context endpoints - AI-optimized textual descriptions.

All endpoints that return AI context via /api/v6/context/*.
"""

from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


from ..types.request_models import (
    BirthDataRequestModel,
    BirthChartDataRequestModel,
    SynastryChartDataRequestModel,
    CompositeChartDataRequestModel,
    TransitChartDataRequestModel,
    PlanetaryReturnDataRequestModel,
    NowSubjectRequestModel,
)
from ..types.response_models import (
    SubjectContextResponseModel,
    ContextResponseModel,
    ReturnContextResponseModel,
)
from ..utils.clock import utc_now
from ..utils.router_utils import (
    build_now_subject,
    build_subject,
    calculate_return_chart_data,
    context_payload,
    create_natal_chart_data,
    create_synastry_chart_data,
    create_composite_chart_data,
    create_transit_chart_data,
    handle_exception,
    parse_precomputed_chart_data,
    resolve_active_points,
    run_heavy,
    subject_context_payload,
)
from ..utils.logging_utils import log_request_with_body

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/context/subject", response_model=SubjectContextResponseModel)
async def subject_context(birth_data_request: BirthDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/subject`

    Builds and returns an astrological subject with AI-optimized context.

    **Parameters:**
    - `subject`: SubjectModel (offline preferred or GeoNames via geonames_username)
    - `active_points`: Optional points override. The other inherited chart-data
      options (`active_aspects`, `distribution_method`, `custom_distribution_weights`,
      `axis_orb_limit`, `point_orb_adjustments`, `point_orb_adjustment_strategy`)
      have no effect on this endpoint.

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `subject`: AstrologicalSubjectModel (serialized)
    """
    log_request_with_body(logger, request, "Subject context request", birth_data_request.model_dump_json())

    try:
        active_points = resolve_active_points(birth_data_request.active_points)
        subject = await run_heavy(build_subject, birth_data_request.subject, active_points=active_points)
        payload = await run_heavy(subject_context_payload, subject)
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/birth-chart", response_model=ContextResponseModel)
async def natal_context(request_body: BirthChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/birth-chart`

    Returns natal chart data with AI-optimized context.

    Supports two modes:
    - **Compute mode** (default): provide `subject` to calculate from scratch.
    - **Pre-computed mode**: provide `chart_data` (from a previous `/chart/*` or
      `/context/*` response) to skip calculation and generate context directly.

    **Parameters:**
    - `subject`: SubjectModel *(required in compute mode)*
    - `chart_data`: dict *(pre-computed chart data, alternative to subject)*
    - `active_points` / `active_aspects` (optional overrides, compute mode only)
    - `distribution_method`, `custom_distribution_weights` (optional, compute mode only)

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Natal context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_natal_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/synastry", response_model=ContextResponseModel)
async def synastry_context(request_body: SynastryChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/synastry`

    Returns synastry chart data with AI-optimized context.

    Supports two modes:
    - **Compute mode**: provide `first_subject` and `second_subject`.
    - **Pre-computed mode**: provide `chart_data` to skip calculation.

    **Parameters:**
    - `first_subject`, `second_subject`: SubjectModel *(required in compute mode)*
    - `chart_data`: dict *(pre-computed chart data, alternative to subjects)*
    - `include_house_comparison`, `include_relationship_score` (flags)
    - `active_points` / `active_aspects` overrides (compute mode only)

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Synastry context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_synastry_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/composite", response_model=ContextResponseModel)
async def composite_context(request_body: CompositeChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/composite`

    Returns composite chart data with AI-optimized context.

    Supports two modes:
    - **Compute mode**: provide `first_subject` and `second_subject`.
    - **Pre-computed mode**: provide `chart_data` to skip calculation.

    **Parameters:**
    - `first_subject`, `second_subject` *(required in compute mode)*
    - `chart_data`: dict *(pre-computed chart data, alternative to subjects)*
    - `active_points` / `active_aspects` overrides (compute mode only)

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Composite context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_composite_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/transit", response_model=ContextResponseModel)
async def transit_context(request_body: TransitChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/transit`

    Returns transit chart data with AI-optimized context.

    Supports two modes:
    - **Compute mode**: provide `first_subject` and `transit_subject`.
    - **Pre-computed mode**: provide `chart_data` to skip calculation.

    **Parameters:**
    - `first_subject`: SubjectModel (natal) *(required in compute mode)*
    - `transit_subject`: SubjectModel (transit moment) *(required in compute mode)*
    - `chart_data`: dict *(pre-computed chart data, alternative to subjects)*
    - `include_house_comparison` flag

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Transit context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_transit_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/solar-return", response_model=ReturnContextResponseModel)
async def solar_return_context(request_body: PlanetaryReturnDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/solar-return`

    Calculates the solar return and returns data with AI-optimized context.

    Supports two modes:
    - **Compute mode**: provide `subject` + search parameters (`year`/`iso_datetime`).
    - **Pre-computed mode**: provide `chart_data` to skip calculation.

    **Parameters:**
    - `subject`: SubjectModel (natal) *(required in compute mode)*
    - `year` or `month`+`year` or `iso_datetime` *(required in compute mode)*
    - `chart_data`: dict *(pre-computed chart data, alternative to subject + search params)*
    - `wheel_type`: "dual"|"single" (affects data model)

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    - `return_type`: "Solar"
    - `wheel_type`: "dual" | "single"
    """
    log_request_with_body(logger, request, "Solar return context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_return_chart_data, request_body, "Solar")
        payload = await run_heavy(context_payload, chart_data)
        payload["return_type"] = "Solar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/context/lunar-return", response_model=ReturnContextResponseModel)
async def lunar_return_context(request_body: PlanetaryReturnDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/context/lunar-return`

    Calculates the lunar return and returns data with AI-optimized context.

    Supports two modes:
    - **Compute mode**: provide `subject` + search parameters.
    - **Pre-computed mode**: provide `chart_data` to skip calculation.

    **Parameters:**
    - Same as solar-return context.

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    - `return_type`: "Lunar"
    - `wheel_type`: "dual" | "single"
    """
    log_request_with_body(logger, request, "Lunar return context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_return_chart_data, request_body, "Lunar")
        payload = await run_heavy(context_payload, chart_data)
        payload["return_type"] = "Lunar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)






@router.post("/api/v6/now/context", response_model=SubjectContextResponseModel)
async def now_context(request_body: NowSubjectRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/now/context`

    Returns an astrological subject with AI context for the current UTC time at Greenwich.

    **Parameters:**
    - `name`, `zodiac_type`, `sidereal_mode`, `perspective_type`, `houses_system_identifier`
    - Also accepted: `active_points`, `custom_ayanamsa_t0`/`custom_ayanamsa_ayan_t0`
      (USER sidereal mode), the `calculate_*` toggles (dignities, nakshatra,
      gauquelin, nutation, local space), `nakshatra_ayanamsa`,
      `active_fixed_stars` and `active_midpoints`.

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `subject`: AstrologicalSubjectModel (serialized)
    """
    log_request_with_body(logger, request, "Current context request", request_body.model_dump_json())

    try:
        utc_datetime = utc_now()

        subject = await run_heavy(build_now_subject, request_body, utc_datetime)

        payload = await run_heavy(subject_context_payload, subject)
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


# ===========================================================================
# Phase 2 Predictive Context Endpoints
# ===========================================================================
