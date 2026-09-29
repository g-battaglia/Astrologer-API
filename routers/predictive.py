"""Predictive API endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import ChartDataFactory, PTOLEMAIC_ASPECTS, PrimaryDirectionsFactory, SecondaryProgressionFactory, SolarArcFactory, to_context
from logging import getLogger
from ..types.request_models import PrimaryDirectionsRequestModel, SecondaryProgressionsRequestModel, SolarArcDirectionsRequestModel
from ..types.response_models import (
    ChartDataResponseModel,
    PrimaryDirectionsContextResponseModel,
    PrimaryDirectionsResponseModel,
    ProgressionChartResponseModel,
    SecondaryProgressionsContextResponseModel,
    SecondaryProgressionsResponseModel,
    SolarArcContextResponseModel,
    SolarArcDirectionsResponseModel,
)
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import EXTENDED_RENDERING_FIELDS, RENDERING_FIELD_DEFAULTS, build_subject, dump, handle_exception, run_heavy

logger = getLogger(__name__)
router = APIRouter()


def _predictive_active_aspects(aspect_orb: float, aspects: "list[str] | None") -> "list[dict]":
    """Build an active-aspects list for a predictive chart wheel from the
    scalar ``aspect_orb`` + optional aspect-name whitelist, so the rendered
    biwheel SVG and aspect grid stay consistent with the cross-aspect table
    computed by the matching ``/advanced/...`` endpoint."""
    names = list(aspects) if aspects is not None else list(PTOLEMAIC_ASPECTS)
    return [{"name": name, "orb": aspect_orb} for name in names]


def _render_progression_chart_payload(chart_data, request_body) -> dict:
    """Render the progression / solar-arc biwheel SVGs + data payload (CPU-heavy,
    call via ``run_heavy``)."""
    from kerykeion import ChartDrawer

    # Same omit-if-default rule as router_utils.render_chart: the pinned
    # kerykeion does not know the extended options, and an unknown keyword raises
    # TypeError in ChartDrawer.__init__ — a 500 on every request, not just the
    # ones that ask for an option.
    #
    # Omit-if-default, by value rather than by truthiness: EXTENDED_RENDERING_FIELDS
    # is no longer all-boolean (glyph_size is a three-valued enum whose default,
    # "medium", is truthy).
    extended = {name: value for name in EXTENDED_RENDERING_FIELDS if (value := getattr(request_body, name, RENDERING_FIELD_DEFAULTS[name])) != RENDERING_FIELD_DEFAULTS[name]}

    drawer = ChartDrawer(
        chart_data,
        theme=request_body.theme or "classic",
        transparent_background=request_body.transparent_background,
        style=getattr(request_body, "style", "classic"),
        show_zodiac_background_ring=getattr(request_body, "show_zodiac_background_ring", True),
        **extended,
    )
    # remove_css_variables is left False to match the main charts router
    # (router_utils.render_chart), so downstream CSS-variable theming applies
    # uniformly to every chart endpoint.
    return {
        "status": "OK",
        "chart_wheel": drawer.generate_wheel_only_svg_string(minify=True),
        "chart_grid": drawer.generate_aspect_grid_only_svg_string(minify=True),
        "chart_data": dump(chart_data),
    }


@router.post("/api/v6/predictive/primary-directions/analysis", response_model=PrimaryDirectionsResponseModel, operation_id="advancedPrimaryDirections")
async def primary_directions(request_body: PrimaryDirectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/primary-directions/analysis`

    Compute primary directions using the Placidus semi-arc method.

    **Parameters:**
    - `subject`: Natal subject.
    - `max_years`: Maximum years to project (default 100).
    - `rate_key`: 'ptolemy' or 'naibod' (default 'ptolemy').
    - `aspects`: Optional list of aspects to calculate.

    **Returns:**
    - `directions`: List of primary directions.
    - `speculum`: Speculum table with RA, declination, semi-arc data.
    """
    log_request_with_body(logger, request, "Primary directions request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        directions = await run_heavy(
            PrimaryDirectionsFactory.compute,
            subject,
            max_years=request_body.max_years,
            rate_key=request_body.rate_key,
            aspects=request_body.aspects,
        )

        speculum = await run_heavy(PrimaryDirectionsFactory.compute_speculum, subject)

        return JSONResponse(
            content={
                "status": "OK",
                "directions": dump(directions),
                "speculum": dump(speculum),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post(
    "/api/v6/predictive/secondary-progressions/analysis",
    response_model=SecondaryProgressionsResponseModel,
    operation_id="advancedSecondaryProgressions",
)
async def secondary_progressions(request_body: SecondaryProgressionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/secondary-progressions/analysis`

    Compute the day-for-a-year secondary-progressed chart for a target
    moment. The mapping is `progressed_days = (target − birth) /
    365.25`; the progressed chart is calculated for that moment at the
    natal location, reusing every natal calculation setting (zodiac
    type, sidereal mode, house system, perspective, active points).

    Pass exactly one of `target_iso_utc_datetime` or `target_year`.

    **Parameters:**
    - `subject`: Natal subject to progress.
    - `target_iso_utc_datetime` / `target_year`: Target moment (exactly one).
    - `active_points`: Points to calculate and use in aspect detection.
    - `compute_aspects`, `aspect_orb`, `aspects`: Progressed-to-natal aspect
      detection (on by default, 3 degree orb, Ptolemaic aspects).
    - `point_orb_adjustments`, `point_orb_adjustment_strategy`: Per-point orb tuning.

    **Returns:**
    - `progressed_subject`: Full `AstrologicalSubjectModel` for the
      progressed moment, identical in shape to a natal subject.
    - `target_iso_utc_datetime`: The resolved target moment (UTC).
    - `ephemeris_iso_utc_datetime`: The ephemeris moment the day-for-a-year
      mapping points at.
    - `progressed_points`: Per-point natal vs progressed comparison with the
      engine's `sign_changed` ingress flag.
    - `progressed_to_natal_aspects`: Progressed-to-natal aspect contacts
      (empty when `compute_aspects=false`).
    """
    log_request_with_body(logger, request, "Secondary progressions request", request_body.model_dump_json())

    try:
        active_points = request_body.active_points
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)
        result = await run_heavy(
            SecondaryProgressionFactory.compute_full,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
            active_points=active_points,
            compute_aspects=request_body.compute_aspects,
            aspect_orb=request_body.aspect_orb,
            aspects=request_body.aspects,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "progressed_subject": dump(result.progressed_subject),
                "target_iso_utc_datetime": result.target_iso_utc_datetime,
                "ephemeris_iso_utc_datetime": result.ephemeris_iso_utc_datetime,
                # Per-point comparison with the engine's sign_changed ingress
                # flag — the whole reason clients stopped diffing sign strings.
                "progressed_points": [p.model_dump() for p in result.progressed_points],
                "progressed_to_natal_aspects": [a.model_dump() for a in result.progressed_to_natal_aspects],
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post(
    "/api/v6/predictive/solar-arc-directions/analysis",
    response_model=SolarArcDirectionsResponseModel,
    operation_id="advancedSolarArcDirections",
)
async def solar_arc_directions(request_body: SolarArcDirectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/solar-arc-directions/analysis`

    Compute the solar arc and the directed-to-natal aspect picture for
    a target moment. The progressed Sun's longitude minus the natal
    Sun's longitude (shortest arc, signed) is the *solar arc*; that
    single arc is applied to every requested natal point.

    Pass exactly one of `target_iso_utc_datetime` or `target_year`.

    **Returns:**
    - `solar_arc_subject`: `SolarArcSubjectModel` carrying the arc,
      directed-point list (with `sign_changed` flag), and
      directed-to-natal aspect contacts.
    """
    log_request_with_body(logger, request, "Solar arc directions request", request_body.model_dump_json())

    try:
        active_points = request_body.active_points
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)
        result = await run_heavy(
            SolarArcFactory.compute,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
            active_points=active_points,
            compute_aspects=request_body.compute_aspects,
            aspect_orb=request_body.aspect_orb,
            aspects=request_body.aspects,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "solar_arc_subject": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/secondary-progressions/chart", response_model=ProgressionChartResponseModel, operation_id="chartSecondaryProgressions")
async def secondary_progressions_chart(request_body: SecondaryProgressionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/secondary-progressions/chart`

    Compute the progressed chart and render a biwheel SVG (natal inner,
    progressed outer).

    **Parameters:**
    - `theme`, `style`, `glyph_size`, `show_zodiac_background_ring`, `transparent_background`
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false)
    - `include_house_comparison`, `axis_orb_limit`, `distribution_method`,
      `custom_distribution_weights`: Chart-data computation options.
    - `language` is not accepted on this route; the SVG is rendered in English.
    - The remaining `/chart/*` rendering options are not accepted here: this route
      always returns wheel + grid, so `split_chart` and the info-panel flags it
      would switch have nothing to act on.

    **Returns:**
    - `status`: "OK"
    - `chart_wheel`: SVG of the biwheel (no aspect grid)
    - `chart_grid`: SVG of the aspect grid (separate panel)
    - `chart_data`: DualChartDataModel (Progression type)
    """
    log_request_with_body(logger, request, "Progression chart request", request_body.model_dump_json())

    try:
        active_points = request_body.active_points
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)
        progressed = await run_heavy(
            SecondaryProgressionFactory.compute,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
        )
        chart_data = await run_heavy(
            ChartDataFactory.create_progression_chart_data,
            subject,
            progressed,
            active_points=active_points,
            # compute_aspects=false is honored the same way /advanced/secondary-
            # progressions honors it: an empty active-aspects list yields an empty
            # aspect table (None would fall back to the factory defaults).
            active_aspects=(_predictive_active_aspects(request_body.aspect_orb, request_body.aspects) if request_body.compute_aspects else []),
            include_house_comparison=request_body.include_house_comparison,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

        payload = await run_heavy(_render_progression_chart_payload, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/solar-arc-directions/chart", response_model=ProgressionChartResponseModel, operation_id="chartSolarArcDirections")
async def solar_arc_chart(request_body: SolarArcDirectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/solar-arc-directions/chart`

    Compute the solar arc directions and render a biwheel SVG (natal
    inner ring, directed outer ring). Houses and angles stay on the
    natal frame; every directable point is shifted forward by the
    solar arc.

    **Parameters:**
    - `theme`, `style`, `glyph_size`, `show_zodiac_background_ring`, `transparent_background`
    - `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`,
      `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note`
      (all default false)
    - `include_house_comparison`, `axis_orb_limit`, `distribution_method`,
      `custom_distribution_weights`: Chart-data computation options.
    - `language` is not accepted on this route; the SVG is rendered in English.
    - The remaining `/chart/*` rendering options are not accepted here: this route
      always returns wheel + grid, so `split_chart` and the info-panel flags it
      would switch have nothing to act on.

    **Returns:**
    - `status`: "OK"
    - `chart_wheel`: SVG of the biwheel (no aspect grid)
    - `chart_grid`: SVG of the aspect grid (separate panel)
    - `chart_data`: DualChartDataModel (Progression type — solar arc
      shares the symbolic-direction structure with progressions)
    """
    log_request_with_body(logger, request, "Solar arc chart request", request_body.model_dump_json())

    try:
        active_points = request_body.active_points
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)
        directed = await run_heavy(
            SolarArcFactory.compute_directed_subject,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
        )
        chart_data = await run_heavy(
            ChartDataFactory.create_progression_chart_data,
            subject,
            directed,
            active_points=active_points,
            active_aspects=_predictive_active_aspects(request_body.aspect_orb, request_body.aspects),
            include_house_comparison=request_body.include_house_comparison,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

        payload = await run_heavy(_render_progression_chart_payload, chart_data, request_body)
        return JSONResponse(content=payload, status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/secondary-progressions/data", response_model=ChartDataResponseModel, operation_id="chartDataSecondaryProgressions")
async def secondary_progressions_chart_data(request_body: SecondaryProgressionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/secondary-progressions/data`

    Compute the progressed chart data (no SVG rendering).

    **Parameters:**
    - `subject`, `target_iso_utc_datetime` / `target_year`, `active_points`,
      `aspect_orb`, `aspects`, `compute_aspects` — as in
      `/advanced/secondary-progressions`.
    - `include_house_comparison`, `axis_orb_limit`, `distribution_method`,
      `custom_distribution_weights`: Chart-data computation options.
    - `language` is not accepted on this route.

    **Returns:**
    - `status`: "OK"
    - `chart_data`: DualChartDataModel (Progression type)
    """
    log_request_with_body(logger, request, "Progression chart-data request", request_body.model_dump_json())

    try:
        active_points = request_body.active_points
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)
        progressed = await run_heavy(
            SecondaryProgressionFactory.compute,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
        )
        # Same aspect configuration as /chart/secondary-progressions, so the
        # data-only endpoint returns the same aspect table as the chart one.
        chart_data = await run_heavy(
            ChartDataFactory.create_progression_chart_data,
            subject,
            progressed,
            active_points=active_points,
            # compute_aspects=false is honored the same way /advanced/secondary-
            # progressions honors it: an empty active-aspects list yields an empty
            # aspect table (None would fall back to the factory defaults).
            active_aspects=(_predictive_active_aspects(request_body.aspect_orb, request_body.aspects) if request_body.compute_aspects else []),
            include_house_comparison=request_body.include_house_comparison,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "chart_data": dump(chart_data),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/secondary-progressions/context", response_model=SecondaryProgressionsContextResponseModel, operation_id="contextSecondaryProgressions")
async def secondary_progressions_context(request_body: SecondaryProgressionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/secondary-progressions/context`

    Compute the day-for-a-year progressed chart and return AI-optimized context.

    Note: this endpoint serialises the progressed *subject* (via ``to_context``),
    which does not include a progressed-to-natal aspect table. The aspect-tuning
    and chart-data fields on the request model (``compute_aspects``,
    ``aspect_orb``, ``aspects``, ``point_orb_adjustments``,
    ``point_orb_adjustment_strategy``, ``axis_orb_limit``,
    ``distribution_method``, ``custom_distribution_weights``,
    ``include_house_comparison``) and the rendering fields (``theme``, ``style``,
    ``glyph_size``, ``transparent_background`` and the ``show_*`` flags)
    therefore only affect the ``/chart`` and ``/chart-data``
    secondary-progression endpoints, not this context path. ``active_points``
    IS honored: it selects the points calculated on the natal and progressed
    subjects. (Unlike solar-arc, whose factory returns an aspect-bearing
    subject model that ``to_context`` can render.)
    """
    log_request_with_body(logger, request, "Secondary progressions context request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject, active_points=request_body.active_points)
        progressed = await run_heavy(
            SecondaryProgressionFactory.compute,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
        )
        return JSONResponse(
            content={
                "status": "OK",
                "context": to_context(progressed),
                "progressed_subject": dump(progressed),
            },
            status_code=200,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/solar-arc-directions/context", response_model=SolarArcContextResponseModel, operation_id="contextSolarArcDirections")
async def solar_arc_context(request_body: SolarArcDirectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/solar-arc-directions/context`

    Compute solar arc directions and return AI-optimized context.
    """
    log_request_with_body(logger, request, "Solar arc context request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject, active_points=request_body.active_points)
        result = await run_heavy(
            SolarArcFactory.compute,
            subject,
            target_iso_utc_datetime=request_body.target_iso_utc_datetime,
            target_year=request_body.target_year,
            active_points=request_body.active_points,
            compute_aspects=request_body.compute_aspects,
            aspect_orb=request_body.aspect_orb,
            aspects=request_body.aspects,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        )
        return JSONResponse(
            content={
                "status": "OK",
                "context": to_context(result),
                "solar_arc_subject": dump(result),
            },
            status_code=200,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/predictive/primary-directions/context", response_model=PrimaryDirectionsContextResponseModel, operation_id="contextPrimaryDirections")
async def primary_directions_context(request_body: PrimaryDirectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/predictive/primary-directions/context`

    Compute primary directions and return AI-optimized context.
    """
    log_request_with_body(logger, request, "Primary directions context request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)
        directions = await run_heavy(
            PrimaryDirectionsFactory.compute,
            subject,
            max_years=request_body.max_years,
            rate_key=request_body.rate_key,
            aspects=request_body.aspects,
        )
        speculum = await run_heavy(PrimaryDirectionsFactory.compute_speculum, subject)

        directions_xml = ["<primary_directions_analysis>"]
        for d in directions:
            directions_xml.append(f'  <direction promissor="{d.promissor}" significator="{d.significator}" aspect="{d.aspect}" arc="{d.arc:.4f}" years="{d.direction_years:.2f}" />')
        directions_xml.append("</primary_directions_analysis>")
        context = "\n".join(directions_xml)

        return JSONResponse(
            content={
                "status": "OK",
                "context": context,
                "directions": dump(directions),
                "speculum": dump(speculum),
            },
            status_code=200,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
