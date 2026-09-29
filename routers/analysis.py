"""Analysis API endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import AspectsFactory, MidpointFactory, PlanetaryNodesFactory, to_context
from logging import getLogger
from ..types.request_models import DeclinationAspectsRequestModel, DualDeclinationAspectsRequestModel, MidpointsRequestModel, PlanetaryNodesRequestModel
from ..types.response_models import DeclinationAspectsResponseModel, MidpointsContextResponseModel, MidpointsResponseModel, PlanetaryNodesResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import build_subject, dump, handle_exception, resolve_active_points, run_heavy

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/analysis/planetary-nodes", response_model=PlanetaryNodesResponseModel, operation_id="advancedPlanetaryNodes")
async def planetary_nodes(request_body: PlanetaryNodesRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/planetary-nodes`

    Compute ascending/descending nodes and perihelion/aphelion for planets.

    Each entry also carries `periapsis`, `apoapsis` and `apsis_kind` — the apsides named for the
    body the orbit turns around: `heliocentric` for a planet (repeating perihelion/aphelion),
    `geocentric` for the Moon (perigee and apogee, the latter being the Black Moon Lilith point).

    **Parameters:**
    - `subject`: Subject defining the calculation moment.
    - `method`: 'mean' or 'osculating' (default 'mean').
    - `planets`: Optional list of planet names to filter.

    **Returns:**
    - `nodes`: List of planetary node data, each with its `periapsis`, `apoapsis` and `apsis_kind`.
    """
    log_request_with_body(logger, request, "Planetary nodes request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)
        result = await run_heavy(
            PlanetaryNodesFactory.from_subject,
            subject,
            method=request_body.method,
            planets=request_body.planets,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "iso_datetime": getattr(result, "iso_datetime", None),
                "julian_day": getattr(result, "julian_day", None),
                "method": request_body.method,
                "nodes": dump(result.nodes),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/analysis/midpoints", response_model=MidpointsResponseModel, operation_id="advancedMidpoints")
async def midpoints(request_body: MidpointsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/midpoints`

    Compute the full midpoint table for a chart, with each midpoint's
    longitude on the shorter arc, sign + position-within-sign, the 90°
    dial position (`longitude % 90`, used by cosmobiology and Uranian
    astrology), and the third points that aspect the midpoint within
    `aspect_orb` degrees.

    **Parameters:**
    - `subject`: Natal/event subject.
    - `active_points`: Optional list of points to use as midpoint
      constituents. Defaults to the 14-point standard set (91 pairs).
      The table is every pair of the requested points, so its size grows
      quadratically — C(n,2). Points with no position in the requested
      perspective are excluded: `Earth` geocentrically, `Sun`
      heliocentrically.
    - `aspect_orb`: Orb in degrees for aspect-to-midpoint detection
      (default 1.0).
    - `aspects`: Optional whitelist of aspect names.
    - `compute_aspects`: If `false`, skip aspect-to-midpoint detection.

    **Returns:**
    - `midpoints`: List of midpoint entries (see `MidpointModel`).
    """
    log_request_with_body(logger, request, "Midpoints request", request_body.model_dump_json())

    try:
        # The requested constituents must also reach the subject build: points
        # outside the subject's default active set would otherwise be missing
        # from the chart and silently dropped from the midpoint table.
        subject = await run_heavy(build_subject, request_body.subject, active_points=request_body.active_points)

        result = await run_heavy(
            MidpointFactory.compute,
            subject,
            active_points=request_body.active_points,
            compute_aspects=request_body.compute_aspects,
            aspect_orb=request_body.aspect_orb,
            aspects=request_body.aspects,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "midpoints": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/analysis/declination-aspects", response_model=DeclinationAspectsResponseModel, operation_id="advancedDeclinationAspects")
async def declination_aspects(request_body: DeclinationAspectsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/declination-aspects`

    Compute declination aspects (parallel / contra-parallel) within a single chart.

    **Parameters:**
    - `subject`: Subject for calculation.
    - `active_points`: Points to include (optional).
    - `orb`: Maximum orb in degrees (default 1.0).

    **Returns:**
    - `aspects`: List of declination aspects.
    """
    log_request_with_body(logger, request, "Declination aspects request", request_body.model_dump_json())

    try:
        active_points = resolve_active_points(request_body.active_points)
        subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)

        aspects = await run_heavy(
            AspectsFactory.single_chart_declination_aspects,
            subject,
            active_points=active_points,
            orb=request_body.orb,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "aspects": dump(aspects),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/analysis/declination-aspects/dual", response_model=DeclinationAspectsResponseModel, operation_id="advancedDeclinationAspectsDual")
async def dual_declination_aspects(request_body: DualDeclinationAspectsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/declination-aspects/dual`

    Compute declination aspects (parallel / contra-parallel) between two charts.

    **Parameters:**
    - `first_subject`, `second_subject`: Two subjects for comparison.
    - `active_points`: Points to include (optional).
    - `orb`: Maximum orb in degrees (default 1.0).

    **Returns:**
    - `aspects`: List of declination aspects.
    """
    log_request_with_body(logger, request, "Dual declination aspects request", request_body.model_dump_json())

    try:
        active_points = resolve_active_points(request_body.active_points)
        first_subject = await run_heavy(build_subject, request_body.first_subject, active_points=active_points)
        second_subject = await run_heavy(build_subject, request_body.second_subject, active_points=active_points)

        aspects = await run_heavy(
            AspectsFactory.dual_chart_declination_aspects,
            first_subject,
            second_subject,
            active_points=active_points,
            orb=request_body.orb,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "aspects": dump(aspects),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/analysis/midpoints/context", response_model=MidpointsContextResponseModel, operation_id="contextMidpoints")
async def midpoints_context(request_body: MidpointsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/midpoints/context`

    Compute the midpoint table and return AI-optimized context.
    """
    log_request_with_body(logger, request, "Midpoints context request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)
        result = await run_heavy(
            MidpointFactory.compute,
            subject,
            active_points=request_body.active_points,
            compute_aspects=request_body.compute_aspects,
            aspect_orb=request_body.aspect_orb,
            aspects=request_body.aspects,
        )
        # MidpointFactory.compute returns an empty list when fewer than 2 of the
        # requested points resolve on the subject; to_context raises on empty
        # lists ("element type is ambiguous"), which would surface as a 500.
        # Mirror /advanced/midpoints, which returns the empty list as a 200.
        return JSONResponse(
            content={
                "status": "OK",
                "context": to_context(result) if result else "No midpoints could be computed: fewer than two of the requested points are available on the subject.",
                "midpoints": dump(result),
            },
            status_code=200,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
