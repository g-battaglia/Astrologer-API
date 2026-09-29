"""Returns API endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from logging import getLogger
from ..types.request_models import (
    HeliocentricReturnContextRequestModel,
    HeliocentricReturnDataRequestModel,
    HeliocentricReturnRequestModel,
    LunarNodeCrossingContextRequestModel,
    LunarNodeCrossingDataRequestModel,
    LunarNodeCrossingRequestModel,
)
from ..types.response_models import HeliocentricReturnChartResponseModel, HeliocentricReturnContextResponseModel, LunarNodeCrossingChartResponseModel, LunarNodeCrossingContextResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import (
    calculate_heliocentric_return_chart_data,
    calculate_lunar_node_crossing_chart_data,
    chart_data_payload,
    chart_payload_from_request,
    context_payload,
    handle_exception,
    parse_precomputed_chart_data,
    run_heavy,
)

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/returns/heliocentric/chart", response_model=HeliocentricReturnChartResponseModel, operation_id="chartHeliocentricReturn")
async def heliocentric_return_chart(request_body: HeliocentricReturnRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/heliocentric/chart`

    Compute a heliocentric return chart for a given planet. The return occurs when
    the planet returns to its natal heliocentric longitude.

    **Parameters:**
    - `subject`: Natal subject.
    - `planet`: Planet whose heliocentric return to compute (e.g. 'Mars').
    - `year` or `iso_datetime`: Search start (exactly one).
    - `direction`: 'next' (default) or 'previous'.
    - `wheel_type`: 'dual' (natal + return biwheel, default) or 'single'.
    - `include_house_comparison`: House overlay for dual wheels.
    - `return_location`: Override the location the return chart is cast for.
    - The rendering options common to every `/chart/*` route, including
      `show_diurnality` and the six extended flags (`show_motion_state`,
      `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`,
      `show_ayanamsa_value`, `show_polar_fallback_note`). "Heliocentric" here
      describes how the return instant is found, not how the wheel is cast: the
      chart takes the subject's own perspective — Apparent Geocentric by default,
      in which case it carries a diurnality line the flag switches off, but a
      heliocentric subject makes the return heliocentric too and the line is then
      omitted.

    **Returns:**
    - `return_type`: "Heliocentric"
    - `planet`: Planet name
    - `wheel_type`: "dual" | "single"
    - `chart_data` + SVG
    """
    log_request_with_body(logger, request, "Heliocentric return chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_heliocentric_return_chart_data, request_body)

        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        payload["return_type"] = "Heliocentric"
        payload["planet"] = request_body.planet
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/returns/heliocentric/data", response_model=HeliocentricReturnChartResponseModel, operation_id="chartDataHeliocentricReturn")
async def heliocentric_return_data(request_body: HeliocentricReturnDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/heliocentric/data`

    Compute heliocentric return chart data (no SVG).

    **Parameters:**
    - `subject`, `planet`, `year`/`iso_datetime`, `direction`, `wheel_type`,
      `include_house_comparison`, `return_location` — as in
      `/chart/heliocentric-return`.
    - `active_points` / `active_aspects` and the other chart-data options.

    **Returns:**
    - `return_type`: "Heliocentric"
    - `planet`: Planet name
    - `wheel_type`: "dual" | "single"
    - `chart_data`: Chart data (no SVG)
    """
    log_request_with_body(logger, request, "Heliocentric return data request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_heliocentric_return_chart_data, request_body)

        payload = await run_heavy(chart_data_payload, chart_data)
        payload["return_type"] = "Heliocentric"
        payload["planet"] = request_body.planet
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/returns/lunar-node-crossing/chart", response_model=LunarNodeCrossingChartResponseModel, operation_id="chartLunarNodeCrossing")
async def lunar_node_crossing_chart(request_body: LunarNodeCrossingRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/lunar-node-crossing/chart`

    Compute the next lunar node crossing return chart. This occurs when the
    Moon's node returns to its natal position.

    **Parameters:**
    - `subject`: Natal subject.
    - `year` or `iso_datetime`: Search start (exactly one).
    - `direction`: 'next' (default) or 'previous'.
    - `wheel_type`: 'dual' (natal + crossing biwheel, default) or 'single'.
    - `include_house_comparison`: House overlay for dual wheels.
    - `return_location`: Override the location the crossing chart is cast for.
    - The rendering options common to every `/chart/*` route, including
      `show_diurnality` and the six extended flags (`show_motion_state`,
      `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`,
      `show_ayanamsa_value`, `show_polar_fallback_note`).

    **Returns:**
    - `return_type`: "Lunar_Node_Crossing"
    - `wheel_type`: "dual" | "single"
    - `chart_data` + SVG
    """
    log_request_with_body(logger, request, "Lunar node crossing chart request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_lunar_node_crossing_chart_data, request_body)

        payload = await run_heavy(chart_payload_from_request, chart_data, request_body)
        payload["return_type"] = "Lunar_Node_Crossing"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/returns/lunar-node-crossing/data", response_model=LunarNodeCrossingChartResponseModel, operation_id="chartDataLunarNodeCrossing")
async def lunar_node_crossing_data(request_body: LunarNodeCrossingDataRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/lunar-node-crossing/data`

    Compute lunar node crossing data (no SVG).

    **Parameters:**
    - `subject`, `year`/`iso_datetime`, `direction`, `wheel_type`,
      `include_house_comparison`, `return_location` — as in
      `/chart/lunar-node-crossing`.
    - `active_points` / `active_aspects` and the other chart-data options.

    **Returns:**
    - `return_type`: "Lunar_Node_Crossing"
    - `wheel_type`: "dual" | "single"
    - `chart_data`: Chart data (no SVG)
    """
    log_request_with_body(logger, request, "Lunar node crossing data request", request_body.model_dump_json())

    try:
        chart_data = await run_heavy(calculate_lunar_node_crossing_chart_data, request_body)

        payload = await run_heavy(chart_data_payload, chart_data)
        payload["return_type"] = "Lunar_Node_Crossing"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/returns/heliocentric/context", response_model=HeliocentricReturnContextResponseModel, operation_id="contextHeliocentricReturn")
async def heliocentric_return_context(request_body: HeliocentricReturnContextRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/heliocentric/context`

    Returns AI-optimized context for a heliocentric return chart.

    Supports two modes:
    - **Pre-computed mode**: provide `chart_data` to skip calculation.
    - **Compute mode**: provide `subject` + `planet` + `year`/`iso_datetime`.

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    - `return_type`: "Heliocentric"
    - `planet`: Planet name (compute mode)
    - `wheel_type`: "dual" | "single"
    """
    log_request_with_body(logger, request, "Heliocentric return context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_heliocentric_return_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        payload["return_type"] = "Heliocentric"
        payload["planet"] = request_body.planet
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/returns/lunar-node-crossing/context", response_model=LunarNodeCrossingContextResponseModel, operation_id="contextLunarNodeCrossing")
async def lunar_node_crossing_context(request_body: LunarNodeCrossingContextRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/returns/lunar-node-crossing/context`

    Returns AI-optimized context for a lunar node crossing chart.

    Supports two modes:
    - **Pre-computed mode**: provide `chart_data` to skip calculation.
    - **Compute mode**: provide `subject` + `year`/`iso_datetime`.

    **Returns:**
    - `status`: "OK"
    - `context`: AI-optimized context string
    - `chart_data`: ChartDataModel
    - `return_type`: "Lunar_Node_Crossing"
    - `wheel_type`: "dual" | "single"
    """
    log_request_with_body(logger, request, "Lunar node crossing context request", request_body.model_dump_json())

    try:
        if request_body.chart_data is not None:
            chart_data = await run_heavy(parse_precomputed_chart_data, request_body.chart_data)
        else:
            chart_data = await run_heavy(calculate_lunar_node_crossing_chart_data, request_body)
        payload = await run_heavy(context_payload, chart_data)
        payload["return_type"] = "Lunar_Node_Crossing"
        payload["wheel_type"] = request_body.wheel_type
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
