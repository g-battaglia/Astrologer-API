"""Transits API endpoints."""

import inspect, json
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from functools import lru_cache
from kerykeion import EphemerisDataFactory, TransitsTimeRangeFactory
from kerykeion.schemas import AstrologicalSubjectModel
from logging import getLogger
from typing import Any, Callable, cast
from ..types.request_models import TransitBatchRequestModel, TransitEventsRequestModel, _parse_iso_range_naive_utc
from ..types.response_models import TransitBatchResponseModel, TransitEventsResponseModel, TransitMomentsResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import build_subject, dump, handle_exception, resolve_active_aspects, resolve_active_points, run_heavy

logger = getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=16)
def _accepts_keyword(target: object, keyword: str) -> bool:
    """True when ``target`` takes ``keyword``; False when it does not or cannot
    be introspected (assume legacy). Lets one handler run unchanged across
    kerykeion releases that added an optional parameter."""
    try:
        return keyword in inspect.signature(cast(Callable[..., Any], target)).parameters
    except (TypeError, ValueError):
        return False


def _transit_ephemeris_factory(
    request_body: TransitEventsRequestModel,
    natal_subject: AstrologicalSubjectModel,
    active_points: list,
    *,
    calculate_dignities: bool = False,
) -> EphemerisDataFactory:
    """Compatibility wrapper around the REST/MCP shared series builder."""
    from ..utils.transit_series import build_transit_series_factory

    return build_transit_series_factory(
        start_date=request_body.start_date,
        end_date=request_body.end_date,
        step_type=request_body.step_type,
        step=request_body.step_days,
        subject_request=request_body.subject,
        natal_subject=natal_subject,
        active_points=active_points,
        calculate_dignities=calculate_dignities,
    )


@router.post("/api/v6/transits/aspect-timeline", response_model=TransitEventsResponseModel, operation_id="advancedTransitAspectTimeline")
async def transit_aspect_timeline(request_body: TransitEventsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/transits/aspect-timeline`

    Compute transit aspect windows over a time range. Identifies when transiting planets
    form aspects to natal positions, with optional exact-moment bisection refinement.

    **Parameters:**
    - `subject`: Natal subject to track transits against.
    - `start_date`, `end_date`: ISO date range (max span 5 years, and at most
      10000 samples at the chosen step).
    - `step_type`: Sampling unit — 'days' (default), 'hours' or 'minutes'.
    - `step_days`: Step size in `step_type` units (default 1).
    - `refine_exact_moments`: Iteratively refine each exact moment between
      adjacent samples (ternary search; default false).
    - `refinement_iterations`: Refinement iterations — precision improves with
      the count: the default 12 gives roughly sub-15-minute precision at daily
      steps, and 30 reaches sub-second.
    - `active_points`, `active_aspects`: Override defaults.
    - `axis_orb_limit`: Override the maximum orb for aspects involving
      ASC/MC/DSC/IC.

    **Returns:**
    - `events`: List of transit events with applying start, exact moment, separating end.
    - `subject`: The natal subject the transits were computed against.
    """
    log_request_with_body(logger, request, "Transit events request", request_body.model_dump_json())

    try:
        active_points = resolve_active_points(request_body.active_points)
        active_aspects = resolve_active_aspects(request_body.active_aspects)
        natal_subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)

        ephemeris_factory = _transit_ephemeris_factory(request_body, natal_subject, active_points)
        ephemeris_points = await run_heavy(ephemeris_factory.get_ephemeris_data_as_astrological_subjects)

        transits_factory = TransitsTimeRangeFactory(
            natal_chart=natal_subject,
            ephemeris_data_points=ephemeris_points,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=request_body.axis_orb_limit,
        )

        result = await run_heavy(
            transits_factory.get_transit_events,
            refine_exact_moments=request_body.refine_exact_moments,
            refinement_iterations=request_body.refinement_iterations,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "events": dump(result.events),
                "subject": dump(result.subject),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/transits/daily-aspects", response_model=TransitMomentsResponseModel, operation_id="advancedTransitDailyAspects")
async def transit_daily_aspects(request_body: TransitEventsRequestModel, request: Request) -> Response:
    """
    **POST** `/api/v6/transits/daily-aspects`

    Compute daily transit snapshots: for each date in the range, return all
    active aspects between transiting planets and natal positions.

    Returns per-day data (date + list of aspects), while transit-aspect-timeline
    returns per-aspect data (aspect + applying/exact/separating window).

    **Parameters:**
    - `subject`: Natal subject to track transits against.
    - `start_date`, `end_date`: ISO date range (max span 5 years, and at most
      10000 samples at the chosen step).
    - `step_type`, `step_days`: Sampling unit and step size (default 1 day).
    - `active_points`, `active_aspects`: Override defaults.
    - `axis_orb_limit`: Override the maximum orb for aspects involving
      ASC/MC/DSC/IC.
    - `include_transit_subjects`: Attach the full transiting chart to every
      snapshot (default false). Roughly one chart per sample: narrow
      `active_points` and the range accordingly.

    **Returns:**
    - `transits`: Per-date snapshots, each with the active aspects at that moment
      and, when `include_transit_subjects` is set, a `subject` with the transiting
      positions, signs, motion state, lunar phase and (with
      `subject.calculate_dignities`) essential dignities.
    - `subject`: The natal subject the transits were computed against.
    - `dates`: ISO dates of the snapshots.
    """
    log_request_with_body(logger, request, "Transit daily aspects request", request_body.model_dump_json())

    try:
        include_subjects = request_body.include_transit_subjects
        if include_subjects and not _accepts_keyword(TransitsTimeRangeFactory.get_transit_moments, "include_subjects"):
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "installed kerykeion does not support include_transit_subjects: remove the flag or upgrade the runtime.",
                    "error_type": "TransitSubjectsUnsupportedError",
                },
                status_code=503,
            )

        active_points = resolve_active_points(request_body.active_points)
        active_aspects = resolve_active_aspects(request_body.active_aspects)
        natal_subject = await run_heavy(build_subject, request_body.subject, active_points=active_points)

        ephemeris_factory = _transit_ephemeris_factory(
            request_body,
            natal_subject,
            active_points,
            # Dignities cost a pass per sample and reach the caller only through
            # the attached subjects: compute them just when they will be returned.
            calculate_dignities=include_subjects and request_body.subject.calculate_dignities,
        )
        ephemeris_points = await run_heavy(ephemeris_factory.get_ephemeris_data_as_astrological_subjects)

        transits_factory = TransitsTimeRangeFactory(
            natal_chart=natal_subject,
            ephemeris_data_points=ephemeris_points,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=request_body.axis_orb_limit,
        )

        moments_kwargs: dict = {"include_subjects": True} if include_subjects else {}
        result = await run_heavy(transits_factory.get_transit_moments, **moments_kwargs)

        def _serialize_body() -> bytes:
            snapshots = dump(result.transits)
            assert isinstance(snapshots, list)
            # Public contract: a snapshot has a `subject` key only when it was
            # requested, keeping default responses byte-identical across
            # kerykeion versions (newer models always carry the field).
            if not include_subjects:
                for snapshot in snapshots:
                    snapshot.pop("subject", None)
            # Same dumps arguments as starlette's JSONResponse.render, so the
            # bytes on the wire match the previous in-loop path.
            return json.dumps(
                {
                    "status": "OK",
                    "transits": snapshots,
                    "subject": dump(result.subject),
                    "dates": result.dates,
                },
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")

        # With subjects attached the body is one chart per sample: dumping and
        # encoding it takes long enough to stall liveness probes if done on the
        # event loop.
        body = await run_heavy(_serialize_body)

        return Response(content=body, media_type="application/json", status_code=200)

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/transits/batch", response_model=TransitBatchResponseModel, operation_id="chartDataTransitBatch")
async def transit_batch_data(request_body: TransitBatchRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/transits/batch`

    Batch transit calculation: computes transit chart data for every date
    in a range, using the same logic as `/chart-data/transit`. Each sampled
    day's transit moment is 12:00 local time at the transit location.

    **Parameters:**
    - `first_subject`: Natal subject.
    - `start_date`, `end_date`: ISO date range (at most 366 sampled dates).
    - `step_days`: Days between samples (1-30, default 1).
    - `location`: Optional transit-location override; latitude, longitude and
      timezone must be provided together (city/nation are independent). When
      omitted, the natal location is used.
    - `active_points` / `active_aspects` and the other chart-data options.

    **Returns:**
    - `status`: "OK"
    - `results`: Array of per-day `{date, chart_data}` entries in a single
      HTTP response.
    """
    log_request_with_body(logger, request, "Transit batch request", request_body.model_dump_json())

    try:
        from datetime import timedelta
        from types import SimpleNamespace
        from kerykeion import ChartDataFactory
        from ..utils.router_utils import (
            resolve_active_aspects,
            normalize_coordinate,
            resolve_nation,
            build_transit_subject,
        )

        def _work() -> dict:
            active_points = resolve_active_points(request_body.active_points)
            active_aspects = resolve_active_aspects(request_body.active_aspects)
            natal_subject = build_subject(request_body.first_subject, active_points=active_points)

            # Same naive-UTC normalization the validator applies to its own
            # copies — re-parsing raw strings would make a tz-aware start
            # incomparable with a naive end (TypeError → 500).
            start_dt, end_dt = _parse_iso_range_naive_utc(request_body.start_date, request_body.end_date)
            step = timedelta(days=request_body.step_days)

            # Transit location: use override or natal
            loc = request_body.location
            t_city = loc.city if loc and loc.city else natal_subject.city
            t_nation = resolve_nation(loc.nation) if loc and loc.nation else natal_subject.nation
            t_lng = normalize_coordinate(loc.longitude) if loc and loc.longitude is not None else natal_subject.lng
            t_lat = normalize_coordinate(loc.latitude) if loc and loc.latitude is not None else natal_subject.lat
            t_tz = loc.timezone if loc and loc.timezone else natal_subject.tz_str

            results = []
            current = start_dt
            while current <= end_dt:
                # Build the transit ring through the shared helper so batch stays
                # in lock-step with the single-date /chart-data/transit path: it
                # inherits the natal subject's sidereal_mode + USER custom-ayanamsa
                # pair and the v6 calc flags (active_fixed_stars, dignities, …).
                # Without the ayanamsa pair a sidereal 'USER' batch would raise.
                transit_request = SimpleNamespace(
                    name="Transit",
                    year=current.year,
                    month=current.month,
                    day=current.day,
                    hour=12,
                    minute=0,
                    second=0,
                    city=t_city,
                    nation=t_nation,
                    longitude=t_lng,
                    latitude=t_lat,
                    timezone=t_tz,
                    geonames_username=None,
                    is_dst=None,
                    altitude=None,
                )
                transit_sub = build_transit_subject(
                    transit_request,
                    reference_subject=natal_subject,
                    active_points=active_points,
                    custom_ayanamsa_t0=request_body.first_subject.custom_ayanamsa_t0,
                    custom_ayanamsa_ayan_t0=request_body.first_subject.custom_ayanamsa_ayan_t0,
                    natal_subject_request=request_body.first_subject,
                )

                chart_data = ChartDataFactory.create_chart_data(
                    "Transit",
                    natal_subject,
                    transit_sub,
                    active_points=active_points,
                    active_aspects=active_aspects,
                    include_house_comparison=request_body.include_house_comparison,
                    axis_orb_limit=request_body.axis_orb_limit,
                    point_orb_adjustments=request_body.point_orb_adjustments,
                    point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
                    distribution_method=request_body.distribution_method,
                    custom_distribution_weights=request_body.custom_distribution_weights,
                )

                results.append(
                    {
                        "date": current.isoformat(),
                        "chart_data": dump(chart_data),
                    }
                )
                current += step

            return {"status": "OK", "results": results}

        payload = await run_heavy(_work)
        return JSONResponse(content=payload, status_code=200)
    except Exception as exc:
        return await handle_exception(exc, request)
