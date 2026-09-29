"""Pickle-safe subject-factory arguments shared with spawned workers."""

from __future__ import annotations

from typing import Any

from ..types.request_models import DEFAULT_NAKSHATRA_AYANAMSA


def subject_factory_kwargs(subject: Any, *, active_points: list[str] | None = None) -> dict[str, Any]:
    """Convert a REST or MCP subject model to from_birth_data kwargs."""
    raw_nation = getattr(subject, "nation", None)
    nation = raw_nation.strip().upper() if isinstance(raw_nation, str) else None
    if not nation or nation.lower() == "null":
        nation = "GB"

    kwargs: dict[str, Any] = {
        "name": subject.name,
        "year": subject.year,
        "month": subject.month,
        "day": subject.day,
        "hour": subject.hour,
        "minute": subject.minute,
        "seconds": getattr(subject, "second", 0) or 0,
        "city": subject.city,
        "nation": nation,
        "lng": subject.longitude,
        "lat": subject.latitude,
        "tz_str": subject.timezone,
        "geonames_username": getattr(subject, "geonames_username", None),
        "online": bool(getattr(subject, "geonames_username", None)),
        "zodiac_type": getattr(subject, "zodiac_type", None) or "Tropical",
        "sidereal_mode": getattr(subject, "sidereal_mode", None),
        "houses_system_identifier": getattr(subject, "houses_system_identifier", None) or "P",
        "perspective_type": getattr(subject, "perspective_type", None) or "Apparent Geocentric",
        "is_dst": getattr(subject, "is_dst", None),
        "altitude": getattr(subject, "altitude", None),
        "active_points": active_points,
        "suppress_geonames_warning": True,
        "custom_ayanamsa_t0": getattr(subject, "custom_ayanamsa_t0", None),
        "custom_ayanamsa_ayan_t0": getattr(subject, "custom_ayanamsa_ayan_t0", None),
    }
    for field in ("calculate_dignities", "calculate_nakshatra", "calculate_gauquelin", "calculate_nutation", "calculate_local_space"):
        if getattr(subject, field, False):
            kwargs[field] = True
    fixed_stars = getattr(subject, "active_fixed_stars", None)
    if fixed_stars:
        kwargs["active_fixed_stars"] = list(fixed_stars)
    ayanamsa = getattr(subject, "nakshatra_ayanamsa", DEFAULT_NAKSHATRA_AYANAMSA)
    if ayanamsa != DEFAULT_NAKSHATRA_AYANAMSA:
        kwargs["nakshatra_ayanamsa"] = ayanamsa
    return kwargs
