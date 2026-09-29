"""Calendar response models."""

from typing import Optional

from pydantic import BaseModel, Field

from kerykeion import (
    IngressModel,
    SignPeriodModel,
    LunarEclipseModel,
    LunationModel,
    MundaneAspectModel,
    SolarEclipseModel,
    StationModel,
    RetrogradePeriodModel,
)


from ..response_core import StatusResponseModel
from .moon import MoonVocWindowEntryModel


class CalendarDayModel(BaseModel):
    """Per-day local layer of the astro-calendar (sun times + planetary hours)."""

    date: str = Field(description="Civil date (YYYY-MM-DD) in the request timezone.")
    sun_times: Optional[dict] = Field(
        default=None,
        description="Sun-times payload for the date (same shape as /api/v6/sun/times), or null when unavailable.",
    )
    planetary_hours: Optional[dict] = Field(
        default=None,
        description="Planetary-hours payload for the date (same shape as /api/v6/sun/planetary-hours), or null when unavailable (e.g. polar day/night).",
    )


class AstroCalendarResponseModel(StatusResponseModel):
    """Response payload for the astro-calendar aggregator."""

    start_date: str = Field(description="Echo of the requested range start.")
    end_date: str = Field(description="Echo of the requested range end.")
    timezone: Optional[str] = Field(default=None, description="Echo of the request timezone (None when no location was provided).")
    ingresses: list[IngressModel] = Field(default_factory=list, description="Sign ingresses in range (with season markers on the Sun's cardinal crossings).")
    lunations: list[LunationModel] = Field(default_factory=list, description="Lunations in range.")
    solar_eclipses: list[SolarEclipseModel] = Field(default_factory=list, description="Solar eclipses in range.")
    lunar_eclipses: list[LunarEclipseModel] = Field(default_factory=list, description="Lunar eclipses in range.")
    retrograde_stations: list[StationModel] = Field(default_factory=list, description="Retrograde/direct stations in range.")
    voc_windows: list[MoonVocWindowEntryModel] = Field(default_factory=list, description="Void-of-course Moon windows intersecting the range.")
    aspectarian: list[MundaneAspectModel] = Field(default_factory=list, description="Exact mundane aspects in range.")
    days: list[CalendarDayModel] = Field(default_factory=list, description="Per-day sun times and planetary hours (when a location is provided).")
    sign_periods: list[SignPeriodModel] = Field(
        default_factory=list,
        description="Where each planet (Moon..Pluto) is, sign by sign, across the range: contiguous stays per planet, clipped to the range and flagged where clipped.",
    )
    retrograde_periods: list[RetrogradePeriodModel] = Field(
        default_factory=list,
        description="Retrograde spans (Mercury..Pluto, Chiron) across the range, clipped to it and flagged where clipped.",
    )
