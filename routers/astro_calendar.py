"""
Astro-calendar aggregator endpoint.

One call returns every layer a calendar month view needs: sign ingresses (with
equinox/solstice markers), lunations, eclipses, retrograde/direct stations,
void-of-course Moon windows, the mundane aspectarian, and — when a location is
provided — per-day sun times and planetary hours.

All astronomy lives in kerykeion's event factories; this handler only sequences
them (each on the bounded heavy pool, yielding between layers so the event loop
and /health stay responsive), filters eclipses to the requested range, and
serialises the layers to one JSON payload.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from logging import getLogger
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion import (
    EclipseFactory,
    LunationFinderFactory,
    MundaneAspectFactory,
    PlanetaryHoursFactory,
    RetrogradeStationFactory,
    SignIngressFactory,
    SunTimesFactory,
    VoidOfCourseMoonFactory,
)
from kerykeion.schemas import KerykeionException

from ..types.request_models import AstroCalendarRequestModel
from ..types.response_models import AstroCalendarResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import dump, handle_exception, run_heavy
from ..utils.astronomy_payloads import _window_payload, _planetary_hours_payload, _sun_times_payload

logger = getLogger(__name__)

router = APIRouter()

# Default aspectarian body set (Sun..Pluto); the Moon is appended when
# include_moon_aspects is true. Mirrors the kerykeion factory default.
_ASPECTARIAN_DEFAULT_POINTS = (
    "Sun",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

# Ingress layer: the finder's own default (Sun..Pluto); the Moon joins on request.
_INGRESS_PLANETS = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
# Sign periods: the Moon too — a calendar reads the Moon's sign every day.
_SIGN_PERIOD_PLANETS = ("Moon",) + _INGRESS_PLANETS
# Retrograde periods: every stationing body the finder knows.
_RETROGRADE_PERIOD_PLANETS = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron")


def _parse_range_utc(start_date: str, end_date: str) -> "tuple[datetime, datetime]":
    """Resolve the request range to naive-UTC datetimes (request-model semantics:
    already validated, date-only end means end of that UTC day)."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)
    if "T" not in end_date and "t" not in end_date and " " not in end_date:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def _civil_dates(start_utc: datetime, end_utc: datetime, tz: ZoneInfo) -> "list[date]":
    """Every civil date (in ``tz``) touched by the UTC range, inclusive."""
    first = start_utc.replace(tzinfo=timezone.utc).astimezone(tz).date()
    last = end_utc.replace(tzinfo=timezone.utc).astimezone(tz).date()
    days: "list[date]" = []
    cur = first
    while cur <= last:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def _day_payload(civil_date: date, latitude: float, longitude: float, tz_str: str, want_sun: bool, want_hours: bool) -> dict:
    """Sun times + planetary hours for one civil date (CPU work, call via run_heavy).

    A per-layer failure (e.g. polar day/night edge the factories cannot frame)
    nulls that field instead of failing the whole month.
    """
    payload: dict = {"date": civil_date.isoformat(), "sun_times": None, "planetary_hours": None}
    if want_sun:
        try:
            sun_times_model = SunTimesFactory.from_date(
                civil_date.year,
                civil_date.month,
                civil_date.day,
                latitude=latitude,
                longitude=longitude,
                tz_str=tz_str,
            )
            payload["sun_times"] = _sun_times_payload(sun_times_model)["sun_times"]
        except KerykeionException:
            pass
    if want_hours:
        try:
            # Noon guarantees the moment falls inside this date's planetary day
            # (sunrise -> next sunrise), whatever the season.
            planetary_hours_model = PlanetaryHoursFactory.from_datetime(
                civil_date.year,
                civil_date.month,
                civil_date.day,
                12,
                0,
                latitude=latitude,
                longitude=longitude,
                tz_str=tz_str,
            )
            payload["planetary_hours"] = _planetary_hours_payload(planetary_hours_model)["planetary_hours"]
        except KerykeionException:
            pass
    return payload


@router.post("/api/v6/calendar", response_model=AstroCalendarResponseModel, operation_id="advancedAstroCalendar")
async def astro_calendar(request_body: AstroCalendarRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/calendar`

    Everything an astrological calendar month needs, in one call: sign
    ingresses (the Sun's cardinal crossings carry equinox/solstice markers),
    lunations, eclipses, retrograde/direct stations, void-of-course Moon
    windows, the mundane aspectarian, and — when an observer location is
    provided — per-day sun times and Chaldean planetary hours.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (UTC, max 45 days — a 6-week grid).
    - `latitude`, `longitude`, `timezone`: Observer (all three together). Required
      only for `include_sun_times` / `include_planetary_hours`.
    - `zodiac_type`, `sidereal_mode`: Zodiac for signs/longitudes in the event layers.
    - `include_*`: Layer toggles, all on by default.
    - `include_moon_aspects`: Adds the Moon to the aspectarian (printed-calendar parity).
    - `include_moon_ingresses`: Adds the Moon's sign ingresses to the ingress layer.
    - `include_sign_periods`: `sign_periods` — where each planet (Moon..Pluto) is,
      sign by sign, across the range (contiguous stays, clipped and flagged).
    - `include_retrograde_periods`: `retrograde_periods` — retrograde spans
      (Mercury..Pluto, Chiron), clipped to the range and flagged.
    - `aspectarian_points`, `aspectarian_aspects`: Aspectarian tuning.

    **Returns:** `status` + the event layers (UTC instants) + `days[]` (local layer).
    """
    log_request_with_body(logger, request, "Astro calendar request", request_body.model_dump_json())

    try:
        start_utc, end_utc = _parse_range_utc(request_body.start_date, request_body.end_date)
        zodiac_kwargs = {
            "zodiac_type": request_body.zodiac_type,
            "sidereal_mode": request_body.sidereal_mode,
        }
        content: dict = {
            "status": "OK",
            "start_date": request_body.start_date,
            "end_date": request_body.end_date,
            "timezone": request_body.timezone,
            "ingresses": [],
            "lunations": [],
            "solar_eclipses": [],
            "lunar_eclipses": [],
            "retrograde_stations": [],
            "voc_windows": [],
            "aspectarian": [],
            "days": [],
            "sign_periods": [],
            "retrograde_periods": [],
        }

        # Each layer runs on the bounded heavy pool; awaiting between layers
        # releases EPHEMERIS_LOCK and keeps the event loop responsive (the
        # same idea as the event scan helper).
        if request_body.include_ingresses:
            ingress_planets = list(_INGRESS_PLANETS)
            if request_body.include_moon_ingresses:
                ingress_planets.append("Moon")
            result = await run_heavy(
                SignIngressFactory.from_iso_range,
                request_body.start_date,
                request_body.end_date,
                ingress_planets,
                **zodiac_kwargs,
            )
            content["ingresses"] = dump(result.ingresses)
            await asyncio.sleep(0)

        if request_body.include_lunations:
            result = await run_heavy(
                LunationFinderFactory.from_iso_range,
                request_body.start_date,
                request_body.end_date,
                **zodiac_kwargs,
            )
            content["lunations"] = dump(result.lunations)
            await asyncio.sleep(0)

        if request_body.include_eclipses:
            # The eclipse factory is start_year/count based; 10 of each type
            # from Jan 1 of the range's start year always covers a <=45-day
            # window inside that year (max 7 eclipses per calendar year).
            # Filter to the range in-handler.
            result = await run_heavy(EclipseFactory.search_global, start_year=start_utc.year, count=10, **zodiac_kwargs)
            # Filter on maximum_jd: JD(UT) bounds derived from the same naive-UTC
            # range the other layers use (JD 2440587.5 = 1970-01-01T00:00Z).
            _EPOCH = datetime(1970, 1, 1)
            start_jd = 2440587.5 + (start_utc - _EPOCH).total_seconds() / 86400.0
            end_jd = 2440587.5 + (end_utc - _EPOCH).total_seconds() / 86400.0
            content["solar_eclipses"] = [dump(e) for e in result.solar_eclipses if start_jd <= e.maximum_jd <= end_jd]
            content["lunar_eclipses"] = [dump(e) for e in result.lunar_eclipses if start_jd <= e.maximum_jd <= end_jd]
            await asyncio.sleep(0)

        if request_body.include_retrograde_stations:
            result = await run_heavy(
                RetrogradeStationFactory.from_iso_range,
                request_body.start_date,
                request_body.end_date,
                **zodiac_kwargs,
            )
            content["retrograde_stations"] = dump(result.stations)
            await asyncio.sleep(0)

        if request_body.include_sign_periods:
            # The Moon is included here on purpose: a calendar reads the Moon's
            # sign every day even when its ingresses are too many to list.
            result = await run_heavy(
                SignIngressFactory.sign_periods_from_iso_range,
                request_body.start_date,
                request_body.end_date,
                list(_SIGN_PERIOD_PLANETS),
                **zodiac_kwargs,
            )
            content["sign_periods"] = dump(result.periods)
            await asyncio.sleep(0)

        if request_body.include_retrograde_periods:
            result = await run_heavy(
                RetrogradeStationFactory.retrograde_periods_from_iso_range,
                request_body.start_date,
                request_body.end_date,
                list(_RETROGRADE_PERIOD_PLANETS),
                **zodiac_kwargs,
            )
            content["retrograde_periods"] = dump(result.periods)
            await asyncio.sleep(0)

        if request_body.include_voc:
            result = await run_heavy(
                VoidOfCourseMoonFactory.from_iso_range,
                request_body.start_date,
                request_body.end_date,
                **zodiac_kwargs,
            )
            tz = ZoneInfo(request_body.timezone) if request_body.timezone else None
            content["voc_windows"] = [_window_payload(w, tz) for w in result.windows]
            await asyncio.sleep(0)

        if request_body.include_aspectarian:
            if request_body.aspectarian_points is not None:
                points = list(request_body.aspectarian_points)
                if request_body.include_moon_aspects and "Moon" not in points:
                    points.append("Moon")
            else:
                points = list(_ASPECTARIAN_DEFAULT_POINTS)
                if request_body.include_moon_aspects:
                    points.append("Moon")
            result = await run_heavy(
                MundaneAspectFactory.from_iso_range,
                request_body.start_date,
                request_body.end_date,
                points,
                request_body.aspectarian_aspects,
                request_body.zodiac_type,
                request_body.sidereal_mode,
            )
            content["aspectarian"] = dump(result.aspects)
            await asyncio.sleep(0)

        want_sun = request_body.include_sun_times
        want_hours = request_body.include_planetary_hours
        if (want_sun or want_hours) and request_body.timezone is not None:
            tz = ZoneInfo(request_body.timezone)
            days: "list[dict]" = []
            for civil_date in _civil_dates(start_utc, end_utc, tz):
                days.append(
                    await run_heavy(
                        _day_payload,
                        civil_date,
                        request_body.latitude,
                        request_body.longitude,
                        request_body.timezone,
                        want_sun,
                        want_hours,
                    )
                )
                await asyncio.sleep(0)
            content["days"] = days

        return JSONResponse(content=content, status_code=200)

    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
