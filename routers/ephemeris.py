"""Ephemeris API endpoints."""

import inspect
import json
from datetime import datetime
from functools import lru_cache
from logging import getLogger
from typing import Any, Callable, cast
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from kerykeion import (
    EphemerisDataFactory,
)
from ..types.request_models import (
    DEFAULT_ACTIVE_POINTS,
    EPHEMERIS_MAX_POINT_CALCULATIONS,
    EPHEMERIS_MAX_SAMPLES,
    FIXED_STAR_WORK_UNIT_WEIGHT,
    _count_ephemeris_samples,
    EphemerisRequestModel,
)
from ..types.response_models import (
    EphemerisResponseModel,
)
from ..utils.router_utils import (
    handle_exception,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body
from ..config.settings import settings

logger = getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=8)
def _ephemeris_factory_supports_fixed_stars(factory: object) -> bool:
    """True when the installed kerykeion ``EphemerisDataFactory`` accepts the
    ``active_fixed_stars`` parameter (Kerykeion >= 6.0.0a75). Cached per
    factory object so the signature inspection runs once per interpreter,
    while monkeypatched test factories still get their own entry."""
    try:
        return "active_fixed_stars" in inspect.signature(cast(Callable[..., Any], factory)).parameters
    except (TypeError, ValueError):  # non-introspectable callable: assume legacy
        return False


@router.post("/api/v6/ephemeris", response_model=EphemerisResponseModel, operation_id="advancedEphemeris")
async def ephemeris_data(request_body: EphemerisRequestModel, request: Request) -> Response:
    """
    **POST** `/api/v6/ephemeris`

    Generate an ephemeris table with planetary positions and house cusps
    over a date range at configurable intervals.

    **Parameters:**
    - `start_date`, `end_date`: ISO date range (at most 732 samples at the
      chosen step, and 30000 point calculations overall).
    - `step_type`: 'days', 'hours', or 'minutes'.
    - `step`: Step size (e.g. 1 day, 6 hours).
    - `latitude`, `longitude`, `timezone`: Observer location.
    - `is_dst`: Daylight-saving disambiguation for ambiguous local times.
    - `zodiac_type`, `sidereal_mode`, `houses_system_identifier`, `perspective_type`: Config.
    - `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0`: Required pair for
      `sidereal_mode='USER'`.
    - `active_points`: Bounded point selection calculated at every sample.
    - `active_fixed_stars`: Bounded fixed-star selection calculated at every sample.
    - `include_houses`, `omit_nulls`: Compact-response controls for large tables.

    **Returns:**
    - `ephemeris`: List of samples with point source/coverage metadata and
      machine-readable omission warnings. Samples carry a `fixed_stars` key
      only when `active_fixed_stars` was requested.
    - `fixed_stars_truncated`: Present only when the requested star list
      exceeded the work budget — how many stars were requested/served and
      which were dropped.
    """
    log_request_with_body(logger, request, "Ephemeris data request", request_body.model_dump_json())

    try:
        requested_fixed_stars = list(request_body.active_fixed_stars or [])
        if requested_fixed_stars and not settings.ephemeris_fixed_stars_enabled:
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "fixed stars temporarily disabled on this deployment: remove active_fixed_stars and retry.",
                    "error_type": "FixedStarsDisabledError",
                },
                status_code=422,
            )
        if requested_fixed_stars and not _ephemeris_factory_supports_fixed_stars(EphemerisDataFactory):
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "installed kerykeion does not support fixed stars in ephemeris: remove active_fixed_stars or upgrade the runtime.",
                    "error_type": "FixedStarsUnsupportedError",
                },
                status_code=503,
            )

        start_dt = datetime.fromisoformat(request_body.start_date)
        end_dt = datetime.fromisoformat(request_body.end_date)

        # Enforce the work budget on the star list HERE, deterministically and
        # out loud: serve the affordable prefix of the request (the caller's
        # own order) and declare the cut in the response. The request model
        # only rejects when the points alone exceed the budget — clients must
        # never need to mirror this cost model to pre-trim their star list.
        # `requested_fixed_stars` stays the caller's original request for the
        # rest of the handler (it decides whether responses carry the
        # fixed_stars key at all); `served_fixed_stars` is the affordable
        # prefix actually forwarded to the factory. Keeping them separate
        # means a zero-capacity truncation still serializes fixed_stars as []
        # instead of silently dropping the key the contract promises.
        served_fixed_stars = requested_fixed_stars
        fixed_stars_truncation: dict | None = None
        if requested_fixed_stars:
            samples = _count_ephemeris_samples(
                request_body.start_date,
                request_body.end_date,
                timezone_name=request_body.timezone,
                is_dst=request_body.is_dst,
                step_type=request_body.step_type,
                step=request_body.step,
            )
            n_points = len(request_body.active_points or DEFAULT_ACTIVE_POINTS)
            affordable = max(
                0,
                (EPHEMERIS_MAX_POINT_CALCULATIONS // max(1, samples) - n_points) // FIXED_STAR_WORK_UNIT_WEIGHT,
            )
            if len(requested_fixed_stars) > affordable:
                dropped = requested_fixed_stars[affordable:]
                fixed_stars_truncation = {
                    "requested": len(requested_fixed_stars),
                    "served": affordable,
                    "dropped": dropped,
                }
                logger.info(
                    "Ephemeris fixed-star budget: serving %d of %d requested stars (%d samples, %d points).",
                    affordable,
                    len(requested_fixed_stars),
                    samples,
                    n_points,
                )
                served_fixed_stars = requested_fixed_stars[:affordable]

        # Only forward the kwarg when there are stars to serve so the
        # star-less path keeps working (and stays byte-identical) on legacy
        # factories that predate the parameter.
        fixed_stars_kwargs: dict = {"active_fixed_stars": served_fixed_stars} if served_fixed_stars else {}

        factory = EphemerisDataFactory(
            start_datetime=start_dt,
            end_datetime=end_dt,
            step_type=request_body.step_type,
            step=request_body.step,
            lat=request_body.latitude,
            lng=request_body.longitude,
            tz_str=request_body.timezone,
            # The engine annotates bool, but passes this through to localize_naive,
            # which accepts None to reject ambiguous times. Preserve that contract.
            is_dst=request_body.is_dst,  # type: ignore[arg-type]
            zodiac_type=request_body.zodiac_type or "Tropical",
            sidereal_mode=request_body.sidereal_mode,
            houses_system_identifier=request_body.houses_system_identifier or "P",
            perspective_type=request_body.perspective_type or "Apparent Geocentric",
            custom_ayanamsa_t0=request_body.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=request_body.custom_ayanamsa_ayan_t0,
            active_points=(list(cast(Any, request_body.active_points)) if request_body.active_points is not None else None),
            # Defense in depth: mirror EphemerisRequestModel's table-specific
            # sample cap inside the factory as well.
            max_days=EPHEMERIS_MAX_SAMPLES,
            max_hours=EPHEMERIS_MAX_SAMPLES,
            max_minutes=EPHEMERIS_MAX_SAMPLES,
            **fixed_stars_kwargs,
        )

        data = await run_heavy(factory.get_ephemeris_data, as_model=True)

        def _serialize_body() -> bytes:
            # Serialization cost scales with samples × nested models: when the
            # caller excluded houses, skip the twelve house-cusp models at dump
            # time instead of serializing and then discarding them (the previous
            # dump-then-overwrite wasted 12 model dumps per sample).
            exclude = None if request_body.include_houses else {"houses"}
            rows = [sample.model_dump(mode="json", exclude=exclude, exclude_none=request_body.omit_nulls) for sample in data]
            for row in rows:
                if not request_body.include_houses:
                    row["houses"] = []
                # Public contract: the fixed_stars key is present only when stars
                # were requested, keeping star-less responses byte-identical
                # across kerykeion versions (newer models always carry the field).
                if not requested_fixed_stars:
                    row.pop("fixed_stars", None)
            # Same dumps arguments as starlette's JSONResponse.render, so the
            # bytes on the wire are identical to the previous in-loop path.
            # The truncation field appears ONLY when a cut happened, keeping
            # untrimmed responses byte-identical to the previous contract.
            payload: dict = {"status": "OK", "ephemeris": rows}
            if fixed_stars_truncation is not None:
                payload["fixed_stars_truncated"] = fixed_stars_truncation
            return json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")

        # Dumping and JSON-encoding hundreds of samples takes hundreds of
        # milliseconds: keep it off the event loop so liveness probes stay
        # responsive while a batch is being serialized.
        body = await run_heavy(_serialize_body)

        return Response(
            content=body,
            media_type="application/json",
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
