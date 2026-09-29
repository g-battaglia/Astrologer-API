"""
Sun-times and planetary-hours endpoints.

Thin REST wrappers over the kerykeion computation engine:
  - ``/api/v6/sun/times``        → :class:`kerykeion.SunTimesFactory`
  - ``/api/v6/sun/planetary-hours``  → :class:`kerykeion.PlanetaryHoursFactory`

All astronomy (sunrise/sunset via the ephemeris backend, Chaldean hour division)
lives in kerykeion; these handlers only adapt the request, call the factory, and
serialise the resulting model to the API's JSON shape.
"""

from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion import PlanetaryHoursFactory, SunTimesFactory

from ..types.request_models import PlanetaryHoursRequestModel, SunTimesRequestModel
from ..types.response_models import PlanetaryHoursResponseModel, SunTimesResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import handle_exception, run_heavy
from ..utils.astronomy_payloads import _duration_hm as _duration_hm, _planetary_hours_payload, _sun_times_payload

logger = getLogger(__name__)

router = APIRouter()


@router.post("/api/v6/sun/times", response_model=SunTimesResponseModel, operation_id="sunTimes")
async def sun_times(request_body: SunTimesRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/sun/times`

    Sunrise, sunset, solar noon and day length for a civil date at a location,
    computed by kerykeion's ``SunTimesFactory`` (apparent, refracted upper limb).
    Civil / nautical / astronomical twilight (Sun at -6 / -12 / -18 degrees) is
    also reported, geometric (no refraction).

    **Returns:** `status` + `sun_times` { date, timezone, latitude, longitude,
    sunrise, sunrise_local, sunset, sunset_local, solar_noon, solar_noon_local,
    day_length, is_polar_day, is_polar_night, civil_dawn(_local),
    civil_dusk(_local), nautical_dawn(_local), nautical_dusk(_local),
    astronomical_dawn(_local), astronomical_dusk(_local) }. Rise/set ``_local``
    strings are HH:MM; twilight ``_local`` strings are full ISO-8601, since an
    evening dusk can fall on the next civil date. A field is null when the event
    does not occur: rise/set on polar day/night, and twilight on polar day —
    during polar night the deeper nautical/astronomical twilight can still be
    present while civil is null.
    """
    log_request_with_body(logger, request, "Sun times request", request_body.model_dump_json())
    try:
        model = await run_heavy(
            SunTimesFactory.from_date,
            request_body.year,
            request_body.month,
            request_body.day,
            latitude=request_body.latitude,
            longitude=request_body.longitude,
            tz_str=request_body.timezone,
        )
        return JSONResponse(content=_sun_times_payload(model), status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/sun/planetary-hours", response_model=PlanetaryHoursResponseModel, operation_id="planetaryHours")
async def planetary_hours(request_body: PlanetaryHoursRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/sun/planetary-hours`

    The 24 Chaldean planetary hours for the planetary day containing the requested
    moment, computed by kerykeion's ``PlanetaryHoursFactory``. Day and night are
    each divided into twelve unequal hours (sunrise→sunset, sunset→next sunrise);
    the first hour is ruled by the weekday's planet, then the Chaldean order cycles.

    **Returns:** `status` + `planetary_hours` { date, timezone, latitude, longitude,
    day_ruler, current_index, current_ruler, current_is_day, sunrise, sunset,
    next_sunrise, hours[] }.
    """
    log_request_with_body(logger, request, "Planetary hours request", request_body.model_dump_json())
    try:
        model = await run_heavy(
            PlanetaryHoursFactory.from_datetime,
            request_body.year,
            request_body.month,
            request_body.day,
            request_body.hour,
            request_body.minute,
            latitude=request_body.latitude,
            longitude=request_body.longitude,
            tz_str=request_body.timezone,
        )
        return JSONResponse(content=_planetary_hours_payload(model), status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
