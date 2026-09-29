"""Calendar request models."""

from __future__ import annotations
from typing import Optional, get_args
from pydantic import Field, field_validator, model_validator
from kerykeion.schemas import (
    SiderealMode,
    ZodiacType,
)
from ..request_core import MUNDANE_ASPECT_NAMES, MUNDANE_ASPECT_POINTS, StrictRequestModel, _check_timezone, _validate_scan_range


class AstroCalendarRequestModel(StrictRequestModel):
    """Request payload for the astro-calendar aggregator.

    One call returns every layer a calendar month view needs: sign ingresses
    (with equinox/solstice markers), lunations, eclipses, retrograde/direct
    stations, void-of-course Moon windows, the mundane aspectarian, and — when
    a location is provided — per-day sun times and planetary hours.
    """

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-07-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC). Maximum span: 45 days (a 6-week month grid).",
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Observer latitude — required (with longitude and timezone) for sun times / planetary hours.",
        examples=[41.9028],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Observer longitude.",
        examples=[12.4964],
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone for the per-day layers (civil dates, local times).",
        examples=["Europe/Rome"],
    )
    zodiac_type: ZodiacType = Field(
        default="Tropical",
        description="Zodiac used for signs/longitudes in the event layers.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )
    # Layer toggles — all on by default.
    include_ingresses: bool = Field(default=True, description="Include the sign-ingress layer.")
    include_lunations: bool = Field(default=True, description="Include the lunation layer.")
    include_eclipses: bool = Field(default=True, description="Include the eclipse layer.")
    include_retrograde_stations: bool = Field(default=True, description="Include the station layer.")
    include_voc: bool = Field(default=True, description="Include the void-of-course Moon window layer.")
    include_aspectarian: bool = Field(default=True, description="Include the mundane aspectarian layer.")
    include_sun_times: bool = Field(default=True, description="Include per-day sun times (requires location).")
    include_planetary_hours: bool = Field(default=True, description="Include per-day planetary hours (requires location).")
    # Aspectarian tuning.
    include_sign_periods: bool = Field(
        default=True,
        description="Include sign_periods: where each planet (Moon..Pluto) is, sign by sign, across the range, clipped to it.",
    )
    include_retrograde_periods: bool = Field(
        default=True,
        description="Include retrograde_periods: retrograde spans (Mercury..Pluto, Chiron) across the range, clipped to it.",
    )
    include_moon_ingresses: bool = Field(
        default=False,
        description="Add the Moon's sign ingresses (~13/month) to the ingresses layer.",
    )
    include_moon_aspects: bool = Field(
        default=True,
        description="Include the Moon in the aspectarian (printed-calendar parity; ~75 extra events/month).",
    )
    aspectarian_points: Optional[list[str]] = Field(
        default=None,
        description="Optional aspectarian body subset (defaults to Sun..Pluto, plus the Moon per include_moon_aspects).",
    )
    aspectarian_aspects: Optional[list[str]] = Field(
        default=None,
        description="Optional aspectarian aspect names (defaults to the five Ptolemaic majors).",
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_payload(self) -> "AstroCalendarRequestModel":
        _validate_scan_range(self.start_date, self.end_date, 45, "45 days (a 6-week month grid)")
        location_fields = (self.latitude, self.longitude, self.timezone)
        provided = [f for f in location_fields if f is not None]
        if provided and len(provided) != 3:
            raise ValueError("latitude, longitude and timezone must be provided together (or all omitted).")
        if not provided and (self.include_sun_times or self.include_planetary_hours):
            raise ValueError("Sun times / planetary hours need an observer: provide latitude, longitude and timezone, or disable include_sun_times and include_planetary_hours.")
        if self.aspectarian_points is not None:
            invalid = [p for p in self.aspectarian_points if p not in MUNDANE_ASPECT_POINTS]
            if invalid:
                raise ValueError(f"Invalid aspectarian point(s): {invalid}. Allowed: {list(MUNDANE_ASPECT_POINTS)}")
            self.aspectarian_points = list(dict.fromkeys(self.aspectarian_points))
        if self.aspectarian_aspects is not None:
            invalid = [a for a in self.aspectarian_aspects if a not in MUNDANE_ASPECT_NAMES]
            if invalid:
                raise ValueError(f"Invalid aspectarian aspect(s): {invalid}. Allowed: {list(MUNDANE_ASPECT_NAMES)}")
            self.aspectarian_aspects = list(dict.fromkeys(self.aspectarian_aspects))
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")
        return self
