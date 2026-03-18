"""
Chart endpoints - SVG rendering.

All endpoints that return rendered SVG charts via /api/v5/chart/*.
"""

from datetime import datetime, timezone
from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..types.request_models import (
    BirthChartRequestModel,
    NowChartRequestModel,
    SynastryChartRequestModel,
    CompositeChartRequestModel,
    TransitChartRequestModel,
    PlanetaryReturnRequestModel,
)
from ..types.response_models import (
    ChartResponseModel,
    ReturnChartResponseModel,
)
from ..utils.router_utils import (
    calculate_return_chart_data,
    chart_payload,
    create_natal_chart_data,
    create_synastry_chart_data,
    create_composite_chart_data,
    create_transit_chart_data,
    handle_exception,
    resolve_active_points,
    resolve_active_aspects,
)
from ..utils.logging_utils import log_request_with_body
from ..utils.get_time_from_google import get_time_from_google
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v5/now/chart", response_model=ChartResponseModel)
async def now_chart(request_body: NowChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/now/chart`

    Returns chart data and SVG for the current UTC time at Greenwich.

    **Parameters:**
    - `name`, configuration, rendering options

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    - `chart`: SVG (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Current time chart request", request_body.model_dump_json())

    try:
        try:
            utc_datetime = get_time_from_google()
        except Exception as time_exc:  # pragma: no cover - fallback path
            logger.warning("Falling back to system UTC time: %s", time_exc)
            utc_datetime = datetime.now(timezone.utc)

        subject = AstrologicalSubjectFactory.from_birth_data(
            name=request_body.name,
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
            zodiac_type=request_body.zodiac_type,
            sidereal_mode=request_body.sidereal_mode,
            perspective_type=request_body.perspective_type,
            houses_system_identifier=request_body.houses_system_identifier,
            active_points=resolve_active_points(request_body.active_points),
            suppress_geonames_warning=True,
        )

        chart_data = ChartDataFactory.create_natal_chart_data(
            subject=subject,
            active_aspects=resolve_active_aspects(request_body.active_aspects),
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/birth-chart", response_model=ChartResponseModel)
async def natal_chart(request_body: BirthChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/birth-chart`

    Returns birth chart data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`
    - `show_degree_indicators`, `show_aspect_icons`
    - `show_zodiac_background_ring` (modern style only)
    - `double_chart_aspect_grid_type` ('list' or 'table', dual charts)
    - `custom_title` (temporary title override, max 40 chars)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    - `chart`: SVG (when split_chart=false)
    - `chart_wheel`, `chart_grid`: SVGs (when split_chart=true)
    """
    log_request_with_body(logger, request, "Birth chart request", request_body.model_dump_json())

    try:
        chart_data = create_natal_chart_data(request_body)
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/synastry", response_model=ChartResponseModel)
async def synastry_chart(request_body: SynastryChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/synastry`

    Returns synastry chart data and a dual-wheel SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid` when split_chart=true)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Synastry chart request", request_body.model_dump_json())

    try:
        chart_data = create_synastry_chart_data(request_body)
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/composite", response_model=ChartResponseModel)
async def composite_chart(request_body: CompositeChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/composite`

    Returns composite chart data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid`)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Composite chart request", request_body.model_dump_json())

    try:
        chart_data = create_composite_chart_data(request_body)
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/transit", response_model=ChartResponseModel)
async def transit_chart(request_body: TransitChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/transit`

    Returns transit data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid`)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Transit chart request", request_body.model_dump_json())

    try:
        chart_data = create_transit_chart_data(request_body)
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/solar-return", response_model=ReturnChartResponseModel)
async def solar_return_chart(request_body: PlanetaryReturnRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/solar-return`

    Returns solar return data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`

    **Returns:**
    - `return_type`: "Solar"
    - `wheel_type`: "dual" | "single"
    - `chart` (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Solar return chart request", request_body.model_dump_json())

    try:
        chart_data = calculate_return_chart_data(request_body, "Solar")
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        payload["return_type"] = "Solar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v5/chart/lunar-return", response_model=ReturnChartResponseModel)
async def lunar_return_chart(request_body: PlanetaryReturnRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v5/chart/lunar-return`

    Returns lunar return data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`

    **Returns:**
    - `return_type`: "Lunar"
    - `wheel_type`: "dual" | "single"
    - `chart` (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Lunar return chart request", request_body.model_dump_json())

    try:
        chart_data = calculate_return_chart_data(request_body, "Lunar")
        payload = chart_payload(
            chart_data,
            request_body.theme,
            request_body.language,
            request_body.split_chart,
            request_body.transparent_background,
            request_body.show_house_position_comparison,
            request_body.show_cusp_position_comparison,
            request_body.show_degree_indicators,
            request_body.show_aspect_icons,
            request_body.custom_title,
            request_body.style,
            request_body.show_zodiac_background_ring,
            request_body.double_chart_aspect_grid_type,
        )
        payload["return_type"] = "Lunar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
