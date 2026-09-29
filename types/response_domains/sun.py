"""Sun response models."""

from typing import Optional

from pydantic import BaseModel, Field

from kerykeion.schemas import ClassicalPlanet


from ..response_core import StatusResponseModel


class SunTimesModel(BaseModel):
    """Sunrise / sunset / solar-noon / day-length for a date + location."""

    date: str = Field(description="Civil date (YYYY-MM-DD) the times are computed for.")
    timezone: str = Field(description="IANA timezone the local strings are expressed in.")
    latitude: float = Field(description="Observer latitude in degrees.")
    longitude: float = Field(description="Observer longitude in degrees.")
    sunrise: Optional[str] = Field(default=None, description="Sunrise, ISO-8601 UTC.")
    sunrise_local: Optional[str] = Field(
        default=None, description="Sunrise local wall-clock time, HH:MM, rounded to the nearest minute; an instant in the last half-minute of the day clamps to 23:59 rather than wrapping to 00:00."
    )
    sunset: Optional[str] = Field(default=None, description="Sunset, ISO-8601 UTC.")
    sunset_local: Optional[str] = Field(
        default=None,
        description="Sunset local wall-clock time, HH:MM, rounded to the nearest minute (23:59-clamped, never wrapped). Above roughly 60 degrees of latitude the paired sunset can genuinely fall past local midnight, so this string can read EARLIER than sunrise_local — the ISO `sunset` field carries the real date; this field cannot.",
    )
    solar_noon: Optional[str] = Field(default=None, description="Solar noon, ISO-8601 UTC.")
    solar_noon_local: Optional[str] = Field(default=None, description="Solar noon local wall-clock time, HH:MM, rounded to the nearest minute.")
    day_length: Optional[str] = Field(default=None, description="Day length, H:MM, rounded to the nearest minute.")
    is_polar_day: bool = Field(default=False, description="True when the Sun stays above the horizon all day.")
    is_polar_night: bool = Field(default=False, description="True when the Sun stays below the horizon all day.")
    civil_dawn: Optional[str] = Field(default=None, description="Civil dawn (Sun at -6 degrees), ISO-8601 UTC.")
    civil_dawn_local: Optional[str] = Field(default=None, description="Civil dawn, ISO-8601 in the request timezone.")
    civil_dusk: Optional[str] = Field(default=None, description="Civil dusk (Sun at -6 degrees), ISO-8601 UTC.")
    civil_dusk_local: Optional[str] = Field(default=None, description="Civil dusk, ISO-8601 in the request timezone (may fall on the next civil date).")
    nautical_dawn: Optional[str] = Field(default=None, description="Nautical dawn (Sun at -12 degrees), ISO-8601 UTC.")
    nautical_dawn_local: Optional[str] = Field(default=None, description="Nautical dawn, ISO-8601 in the request timezone.")
    nautical_dusk: Optional[str] = Field(default=None, description="Nautical dusk (Sun at -12 degrees), ISO-8601 UTC.")
    nautical_dusk_local: Optional[str] = Field(default=None, description="Nautical dusk, ISO-8601 in the request timezone (may fall on the next civil date).")
    astronomical_dawn: Optional[str] = Field(default=None, description="Astronomical dawn (Sun at -18 degrees), ISO-8601 UTC.")
    astronomical_dawn_local: Optional[str] = Field(default=None, description="Astronomical dawn, ISO-8601 in the request timezone.")
    astronomical_dusk: Optional[str] = Field(default=None, description="Astronomical dusk (Sun at -18 degrees), ISO-8601 UTC.")
    astronomical_dusk_local: Optional[str] = Field(default=None, description="Astronomical dusk, ISO-8601 in the request timezone (may fall on the next civil date).")


class SunTimesResponseModel(StatusResponseModel):
    """Response payload for the sun-times endpoint."""

    sun_times: SunTimesModel


class PlanetaryHourModel(BaseModel):
    """One planetary hour in the day's 24-hour Chaldean sequence."""

    index: int = Field(description="1-based position in the 24-hour sequence (1..24).")
    ruler: ClassicalPlanet = Field(description="Classical ruling planet of the hour.")
    is_day: bool = Field(description="True for the 12 day hours (sunrise→sunset), false for night.")
    start: str = Field(description="Hour start, ISO-8601 UTC.")
    end: str = Field(description="Hour end, ISO-8601 UTC.")


class PlanetaryHoursModel(BaseModel):
    """Planetary-hour state for a requested moment plus the full 24-hour table."""

    date: str = Field(description="Civil date of the planetary day's sunrise (YYYY-MM-DD).")
    timezone: str = Field(description="IANA timezone identifier.")
    latitude: float = Field(description="Observer latitude in degrees.")
    longitude: float = Field(description="Observer longitude in degrees.")
    day_ruler: ClassicalPlanet = Field(description="Planet ruling the whole day (by weekday).")
    current_ruler: ClassicalPlanet = Field(description="Ruler of the hour containing the requested moment.")
    current_index: int = Field(description="1-based index of the current hour.")
    current_is_day: bool = Field(description="Whether the current hour is a day hour.")
    sunrise: str = Field(description="Sunrise opening the day hours, ISO-8601 UTC.")
    sunset: str = Field(description="Sunset dividing day and night hours, ISO-8601 UTC.")
    next_sunrise: str = Field(description="Sunrise closing the night hours, ISO-8601 UTC.")
    hours: list[PlanetaryHourModel] = Field(min_length=24, max_length=24, description="All 24 planetary hours in order.")


class PlanetaryHoursResponseModel(StatusResponseModel):
    """Response payload for the planetary-hours endpoint."""

    planetary_hours: PlanetaryHoursModel
