"""
Chart endpoints - SVG rendering.

All endpoints that return rendered SVG charts via /api/v6/chart/*.
"""

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
    build_now_subject,
    calculate_return_chart_data,
    chart_payload_from_request,
    create_natal_chart_data,
    create_synastry_chart_data,
    create_composite_chart_data,
    create_transit_chart_data,
    handle_exception,
    resolve_active_points,
    resolve_active_aspects,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body
from ..utils.clock import utc_now
from kerykeion import ChartDataFactory

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/now/chart", response_model=ChartResponseModel)
async def now_chart(request_body: NowChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/now/chart`

    Returns chart data and SVG for the current UTC time at Greenwich.

    **Parameters:**
    - `name`, configuration, rendering options
    - `show_diurnality` (print the Sun above/below the horizon in the info panel;
      no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    - `chart`: SVG (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Current time chart request", request_body.model_dump_json())

    try:
        utc_datetime = utc_now()

        subject = await run_heavy(build_now_subject, request_body, utc_datetime)

        chart_data = await run_heavy(
            ChartDataFactory.create_chart_data,
            "Natal",
            first_subject=subject,
            active_points=resolve_active_points(request_body.active_points),
            active_aspects=resolve_active_aspects(request_body.active_aspects),
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/birth-chart", response_model=ChartResponseModel)
async def natal_chart(request_body: BirthChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/birth-chart`

    Returns birth chart data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `split_chart`, `transparent_background`
    - `show_degree_indicators`, `show_aspect_icons`
    - `show_zodiac_background_ring`, `glyph_size` (modern style only)
    - `show_diurnality` (print the Sun above/below the horizon in the info panel;
      no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `custom_title` (temporary title override, max 40 chars)
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)
    - Dual-chart-only options, accepted but with no effect on this single natal
      wheel: `show_house_position_comparison`, `show_cusp_position_comparison`,
      `double_chart_aspect_grid_type`

    **Returns:**
    - `status`: "OK"
    - `chart_data`: ChartDataModel
    - `chart`: SVG (when split_chart=false)
    - `chart_wheel`, `chart_grid`: SVGs (when split_chart=true)
    """
    log_request_with_body(logger, request, "Birth chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(create_natal_chart_data, request_body)
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/synastry", response_model=ChartResponseModel)
async def synastry_chart(request_body: SynastryChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/synastry`

    Returns synastry chart data and a dual-wheel SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `glyph_size`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `show_diurnality` (Sun above/below the horizon
      in the info panel; no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `double_chart_aspect_grid_type`, `custom_title`
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid` when split_chart=true)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Synastry chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(create_synastry_chart_data, request_body)
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/composite", response_model=ChartResponseModel)
async def composite_chart(request_body: CompositeChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/composite`

    Returns composite chart data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `glyph_size`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `show_diurnality` (Sun above/below the horizon
      in the info panel; no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `double_chart_aspect_grid_type`, `custom_title`
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid`)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Composite chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(create_composite_chart_data, request_body)
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/transit", response_model=ChartResponseModel)
async def transit_chart(request_body: TransitChartRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/transit`

    Returns transit data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `glyph_size`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `show_diurnality` (Sun above/below the horizon
      in the info panel; no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `double_chart_aspect_grid_type`, `custom_title`
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)

    **Returns:**
    - `chart` (or `chart_wheel` + `chart_grid`)
    - `chart_data`
    """
    log_request_with_body(logger, request, "Transit chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(create_transit_chart_data, request_body)
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/solar-return", response_model=ReturnChartResponseModel)
async def solar_return_chart(request_body: PlanetaryReturnRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/solar-return`

    Returns solar return data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `glyph_size`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `show_diurnality` (Sun above/below the horizon
      in the info panel; no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `double_chart_aspect_grid_type`, `custom_title`
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)

    **Returns:**
    - `return_type`: "Solar"
    - `wheel_type`: "dual" | "single"
    - `chart` (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Solar return chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_return_chart_data, request_body, "Solar")
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        payload["return_type"] = "Solar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/chart/lunar-return", response_model=ReturnChartResponseModel)
async def lunar_return_chart(request_body: PlanetaryReturnRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/chart/lunar-return`

    Returns lunar return data and rendered SVG chart.

    **Parameters:**
    - `theme`, `language`, `style`, `glyph_size`, `split_chart`, `transparent_background`
    - `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`
    - `show_zodiac_background_ring`, `show_diurnality` (Sun above/below the horizon
      in the info panel; no effect with `split_chart`, which returns no panel)
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false: station labels on the wheel, OOB badges in the point
      tables, dashed separating aspects, and three info-panel additions —
      relationship score, ayanamsa degrees, polar house-system substitution)
    - `double_chart_aspect_grid_type`, `custom_title`
    - `external_view`, `auto_size`, `padding`, `colors_settings`, `language_pack`
      (advanced rendering: glyphs outside the wheel, SVG sizing and padding,
      color and label overrides)

    **Returns:**
    - `return_type`: "Lunar"
    - `wheel_type`: "dual" | "single"
    - `chart` (or `chart_wheel` + `chart_grid`)
    """
    log_request_with_body(logger, request, "Lunar return chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_return_chart_data, request_body, "Lunar")
        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        payload["return_type"] = "Lunar"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
