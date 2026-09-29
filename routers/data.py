"""
Chart data endpoints - JSON data only.

All endpoints that return chart data without SVG rendering via /api/v6/chart-data/*.
"""

from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..types.request_models import (
    BirthDataRequestModel,
    BirthChartDataRequestModel,
    NowSubjectRequestModel,
    SynastryChartDataRequestModel,
    CompositeChartDataRequestModel,
    TransitChartDataRequestModel,
    PlanetaryReturnDataRequestModel,
)
from ..types.response_models import (
    ChartDataResponseModel,
    SubjectResponseModel,
    CompatibilityScoreResponseModel,
)
from ..utils.clock import utc_now
from ..utils.router_utils import (
    build_now_subject,
    build_subject,
    calculate_return_chart_data,
    chart_data_payload,
    create_natal_chart_data,
    create_synastry_chart_data,
    create_composite_chart_data,
    create_transit_chart_data,
    dump,
    handle_exception,
    parse_precomputed_chart_data,
    resolve_active_points,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body
from kerykeion.schemas import KerykeionException

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/subject", response_model=SubjectResponseModel)
async def subject_data(birth_data_request: BirthDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/subject`

    Builds and returns an astrological subject.

    **Parameters:**
    - `subject`: SubjectModel (offline preferred or GeoNames via geonames_username)
    - `active_points`: Optional points override. The other inherited chart-data
      options (`active_aspects`, `distribution_method`, `custom_distribution_weights`,
      `axis_orb_limit`, `point_orb_adjustments`, `point_orb_adjustment_strategy`)
      have no effect on this endpoint.

    **Returns:**
    - `status`: "OK"
    - `subject`: AstrologicalSubjectModel (serialized)
    """
    log_request_with_body(logger, request, "Subject data request", birth_data_request.model_dump_json())

    try:
        active_points = resolve_active_points(birth_data_request.active_points)
        subject = await run_heavy(build_subject, birth_data_request.subject, active_points=active_points)
        return JSONResponse(content={"status": "OK", "subject": dump(subject)}, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/now/subject", response_model=SubjectResponseModel)
async def now_subject(request_body: NowSubjectRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/now/subject`

    Returns an astrological subject for the current UTC time at Greenwich.

    **Parameters:**
    - `name`, `zodiac_type`, `sidereal_mode`, `perspective_type`, `houses_system_identifier`
    - Also accepted: `active_points`, `custom_ayanamsa_t0`/`custom_ayanamsa_ayan_t0`
      (USER sidereal mode), the `calculate_*` toggles (dignities, nakshatra,
      gauquelin, nutation, local space), `nakshatra_ayanamsa`,
      `active_fixed_stars` and `active_midpoints`.

    **Returns:**
    - `status`: "OK"
    - `subject`: AstrologicalSubjectModel
    """
    log_request_with_body(logger, request, "Current subject request", request_body.model_dump_json())

    try:
        utc_datetime = utc_now()

        subject = await run_heavy(build_now_subject, request_body, utc_datetime)

        return JSONResponse(content={"status": "OK", "subject": dump(subject)}, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/compatibility-score", response_model=CompatibilityScoreResponseModel)
async def compatibility_score(request_body: SynastryChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/compatibility-score`

    Calculates Ciro Discepolo compatibility score between two subjects.

    **Parameters:**
    - `first_subject`, `second_subject`: SubjectModel
    - `active_points` / `active_aspects` overrides
    - `chart_data`: Pre-computed synastry chart data (alternative to the two
      subjects; if both are sent, `chart_data` wins and nothing is recomputed).
      Must have been computed with `include_relationship_score=true`.

    **Returns:**
    - `status`: "OK"
    - `score`: Compatibility score value
    - `score_description`: Text description of score
    - `is_destiny_sign`: Boolean indicating destiny sign relationship
    - `aspects`: List of aspects used in score calculation
    - `score_breakdown`: Per-rule contributions to the score
    - `chart_data`: Full synastry chart data
    """
    log_request_with_body(logger, request, "Compatibility score request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
            # Non-synastry chart_data kinds have no relationship_score attribute
            # at all — getattr keeps that a 4xx instead of an AttributeError 500.
            if not getattr(chart_data, "relationship_score", None):
                raise KerykeionException("The provided chart_data has no relationship_score. Pass synastry chart data computed with include_relationship_score=true.")
        else:
            # This endpoint's whole purpose is the relationship score, so a request
            # that disables it can never succeed — reject it as a client error (400)
            # rather than letting the downstream None surface as a 500.
            if not request_body.include_relationship_score:
                raise KerykeionException("include_relationship_score must be true for /compatibility-score. Use /api/v6/chart-data/synastry if you only need the chart.")

            chart_data = await run_heavy(create_synastry_chart_data, request_body)

            if not chart_data.relationship_score:  # pragma: no cover - defensive
                raise KerykeionException("Relationship score computation failed. Verify that first_subject and second_subject have valid birth data.")

        return JSONResponse(
            content={
                "status": "OK",
                "score": chart_data.relationship_score.score_value,
                "score_description": chart_data.relationship_score.score_description,
                "is_destiny_sign": chart_data.relationship_score.is_destiny_sign,
                "aspects": dump(chart_data.relationship_score.aspects),
                "score_breakdown": dump(chart_data.relationship_score.score_breakdown),
                "chart_data": dump(chart_data),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart-data/birth-chart", response_model=ChartDataResponseModel)
async def natal_chart_data(request_body: BirthChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/birth-chart`

    Returns full natal chart data without SVG rendering.

    **Parameters:**
    - `subject`: SubjectModel
    - `active_points` / `active_aspects` (optional overrides)
    - `distribution_method`, `custom_distribution_weights` (optional)
    - `chart_data`: Pre-computed chart data (alternative to `subject`; if both
      are sent, `chart_data` wins and nothing is recomputed)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Natal chart data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_natal_chart_data, request_body)
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart-data/synastry", response_model=ChartDataResponseModel)
async def synastry_chart_data(request_body: SynastryChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/synastry`

    Returns synastry chart data comparing two subjects; no SVG rendering.

    **Parameters:**
    - `first_subject`, `second_subject`: SubjectModel
    - `include_house_comparison`, `include_relationship_score` (flags)
    - `active_points` / `active_aspects` overrides
    - `chart_data`: Pre-computed chart data (alternative to the two subjects;
      if both are sent, `chart_data` wins and nothing is recomputed)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Synastry chart data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_synastry_chart_data, request_body)
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart-data/composite", response_model=ChartDataResponseModel)
async def composite_chart_data(request_body: CompositeChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/composite`

    Returns midpoint composite chart data (no SVG rendering).

    **Parameters:**
    - `first_subject`, `second_subject`
    - `active_points` / `active_aspects` overrides
    - `chart_data`: Pre-computed chart data (alternative to the two subjects;
      if both are sent, `chart_data` wins and nothing is recomputed)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Composite chart data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_composite_chart_data, request_body)
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart-data/transit", response_model=ChartDataResponseModel)
async def transit_chart_data(request_body: TransitChartDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/transit`

    Returns transit analysis data (current/selected transits to natal chart), no SVG.

    **Parameters:**
    - `first_subject`: SubjectModel (natal)
    - `transit_subject`: SubjectModel (transit moment)
    - `include_house_comparison` flag
    - `chart_data`: Pre-computed chart data (alternative to the two subjects;
      if both are sent, `chart_data` wins and nothing is recomputed)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Transit chart data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(create_transit_chart_data, request_body)
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)




@router.post("/api/v6/chart-data/solar-return", response_model=ChartDataResponseModel)
async def solar_return_data(request_body: PlanetaryReturnDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/solar-return`

    Calculates the solar return for a given year/month/instant and returns data only.

    **Parameters:**
    - `subject`: SubjectModel (natal)
    - `year` or `month`+`year` or `iso_datetime`
    - `wheel_type`: "dual"|"single" (affects data model)
    - `chart_data`: Pre-computed chart data (alternative to `subject` + search
      parameters; if both are sent, `chart_data` wins and nothing is recomputed)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Solar return data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_return_chart_data, request_body, "Solar")
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart-data/lunar-return", response_model=ChartDataResponseModel)
async def lunar_return_data(request_body: PlanetaryReturnDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart-data/lunar-return`

    Calculates the lunar return and returns data only.

    **Parameters:**
    - Same as solar-return chart-data (including the pre-computed `chart_data`
      mode, which wins over `subject` when both are sent).

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    """
    log_request_with_body(logger, request, "Lunar return data request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_return_chart_data, request_body, "Lunar")
        payload = await run_heavy(chart_data_payload, chart_data)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
