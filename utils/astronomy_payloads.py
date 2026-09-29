"""Shared serialization for sun and void-of-course Moon calculations."""

from datetime import timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from kerykeion.schemas import PlanetaryHoursModel as KrPlanetaryHoursModel
from kerykeion.schemas import SunTimesModel as KrSunTimesModel
from kerykeion.schemas import VoidOfCourseAspectModel, VoidOfCourseMoonModel, VoidOfCourseWindowModel

from .router_utils import iso_utc, iso_utc_opt, local_hm, local_iso


def _duration_hm(span: Optional[timedelta]) -> Optional[str]:
    """Format a duration as ``H:MM``, rounded to the nearest minute, or ``None``.

    Rounded rather than floored, for the same reason as :func:`local_hm`: a day
    length of 16:19:52 is 16:20, and truncating it lost up to 59 s on about half
    of all values. ``int(x + 0.5)`` rather than ``round()`` because the latter
    rounds half to even, which would send 16:19:30 down to 16:19 while sending
    16:20:30 up to 16:21 — a rule no almanac uses and nobody would predict.
    Durations here are non-negative, so the shift is unambiguous.
    """
    if span is None:
        return None
    total_minutes = int(span.total_seconds() / 60.0 + 0.5)
    return f"{total_minutes // 60}:{total_minutes % 60:02d}"


def _sun_times_payload(model: KrSunTimesModel) -> dict:
    """Serialise a kerykeion ``SunTimesModel`` to the API JSON shape."""
    tz = ZoneInfo(model.timezone)
    return {
        "status": "OK",
        "sun_times": {
            "date": model.date,
            "timezone": model.timezone,
            "latitude": model.latitude,
            "longitude": model.longitude,
            "sunrise": iso_utc_opt(model.sunrise),
            "sunrise_local": local_hm(model.sunrise, tz),
            "sunset": iso_utc_opt(model.sunset),
            "sunset_local": local_hm(model.sunset, tz),
            "solar_noon": iso_utc_opt(model.solar_noon),
            "solar_noon_local": local_hm(model.solar_noon, tz),
            "day_length": _duration_hm(model.day_length),
            "is_polar_day": model.is_polar_day,
            "is_polar_night": model.is_polar_night,
            # Twilight dusk can fall in the small hours of the next civil date
            # (evening crossing), so the local strings use local_iso (date + time),
            # unlike the same-day sunrise/sunset which stay HH:MM.
            "civil_dawn": iso_utc_opt(model.civil_dawn),
            "civil_dawn_local": local_iso(model.civil_dawn, tz) if model.civil_dawn else None,
            "civil_dusk": iso_utc_opt(model.civil_dusk),
            "civil_dusk_local": local_iso(model.civil_dusk, tz) if model.civil_dusk else None,
            "nautical_dawn": iso_utc_opt(model.nautical_dawn),
            "nautical_dawn_local": local_iso(model.nautical_dawn, tz) if model.nautical_dawn else None,
            "nautical_dusk": iso_utc_opt(model.nautical_dusk),
            "nautical_dusk_local": local_iso(model.nautical_dusk, tz) if model.nautical_dusk else None,
            "astronomical_dawn": iso_utc_opt(model.astronomical_dawn),
            "astronomical_dawn_local": local_iso(model.astronomical_dawn, tz) if model.astronomical_dawn else None,
            "astronomical_dusk": iso_utc_opt(model.astronomical_dusk),
            "astronomical_dusk_local": local_iso(model.astronomical_dusk, tz) if model.astronomical_dusk else None,
        },
    }


def _planetary_hours_payload(model: KrPlanetaryHoursModel) -> dict:
    """Serialise a kerykeion ``PlanetaryHoursModel`` to the API JSON shape."""
    idx = model.current_index - 1
    return {
        "status": "OK",
        "planetary_hours": {
            "date": model.date,
            "timezone": model.timezone,
            "latitude": model.latitude,
            "longitude": model.longitude,
            "day_ruler": model.day_ruler,
            "current_index": model.current_index,
            "current_ruler": model.current_ruler,
            "current_is_day": model.hours[idx].is_diurnal if 0 <= idx < len(model.hours) else False,
            "sunrise": iso_utc(model.sunrise),
            "sunset": iso_utc(model.sunset),
            "next_sunrise": iso_utc(model.next_sunrise),
            "hours": [
                {
                    "index": hour.index,
                    "ruler": hour.ruler,
                    "is_day": hour.is_diurnal,
                    "start": iso_utc(hour.start),
                    "end": iso_utc(hour.end),
                }
                for hour in model.hours
            ],
        },
    }


def _aspect_payload(aspect: Optional[VoidOfCourseAspectModel], tz: Optional[ZoneInfo]) -> Optional[dict]:
    """Serialise an aspect event to the API JSON shape, or ``None``.

    ``time_local`` is ``None`` when no timezone is available (the windows range
    endpoint makes the timezone optional; the single-moment endpoint always has one).
    """
    if aspect is None:
        return None
    return {
        "planet": aspect.planet,
        "aspect": aspect.aspect,
        "degrees": aspect.aspect_degrees,
        "time": iso_utc(aspect.exact_time),
        "time_local": local_iso(aspect.exact_time, tz) if tz else None,
    }


def _moon_voc_payload(model: VoidOfCourseMoonModel, tz: ZoneInfo) -> dict:
    """Serialise a kerykeion ``VoidOfCourseMoonModel`` to the API JSON shape."""
    return {
        "status": "OK",
        "moon_voc": {
            "is_void": model.is_void_of_course,
            "moon_sign": model.moon_sign,
            "next_sign": model.next_sign,
            "ingress": iso_utc(model.ingress),
            "ingress_local": local_iso(model.ingress, tz),
            "void_start": iso_utc(model.void_start),
            "void_start_local": local_iso(model.void_start, tz),
            "void_end": iso_utc(model.void_end),
            "void_end_local": local_iso(model.void_end, tz),
            "last_aspect": _aspect_payload(model.last_aspect, tz),
            "next_aspect": _aspect_payload(model.next_aspect, tz),
        },
    }


def _window_payload(window: VoidOfCourseWindowModel, tz: Optional[ZoneInfo]) -> dict:
    """Serialise a void window to the API JSON shape (local fields only with a tz)."""
    return {
        "moon_sign": window.moon_sign,
        "next_sign": window.next_sign,
        "void_start": iso_utc(window.void_start),
        "void_start_local": local_iso(window.void_start, tz) if tz else None,
        "void_end": iso_utc(window.void_end),
        "void_end_local": local_iso(window.void_end, tz) if tz else None,
        "duration_minutes": window.duration_minutes,
        "last_aspect": _aspect_payload(window.last_aspect, tz),
    }
