"""Events request models."""

from __future__ import annotations
from typing import Literal, Optional, get_args
from pydantic import Field, model_validator
from kerykeion.schemas import (
    SiderealMode,
    ZodiacType,
)
from ..request_core import MUNDANE_ASPECT_NAMES, MUNDANE_ASPECT_POINTS, StrictRequestModel, SubjectModel, _validate_scan_range


class EclipseSearchRequestModel(StrictRequestModel):
    """Request payload for searching solar and lunar eclipses."""

    model_config = {"extra": "forbid"}

    latitude: Optional[float] = Field(
        default=None,
        description="Latitude for location-specific eclipse search. Omit for global search.",
        ge=-90,
        le=90,
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude for location-specific eclipse search. Omit for global search.",
        ge=-180,
        le=180,
    )
    start_year: int = Field(
        default=2025,
        description=("Year to start searching from (astronomical numbering: 0 = 1 BCE, -1 = 2 BCE, etc.). Supports range -13200 to 9999."),
        ge=-13200,
        le=9999,
    )
    count: int = Field(
        default=5,
        description="Number of eclipses to return.",
        ge=1,
        le=50,
    )

    @model_validator(mode="after")
    def validate_location_pair(self) -> "EclipseSearchRequestModel":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude for a local search, or omit both for a global search.")
        return self


class LunationsRequestModel(StrictRequestModel):
    """Request payload for finding lunations (New/First Quarter/Full/Last Quarter)."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-12-31'.",
    )
    phases: Optional[list[str]] = Field(
        default=None,
        description="Optional subset of 'new', 'first_quarter', 'full', 'last_quarter'.",
    )

    @model_validator(mode="after")
    def validate_range(self) -> "LunationsRequestModel":
        from datetime import datetime, timezone

        try:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError(f"start_date/end_date must be ISO dates: {exc}")
        # fromisoformat returns aware datetimes for offset inputs; comparing a
        # naive with an aware datetime raises TypeError (surfacing as a 500, not
        # a 422), so normalize both to naive UTC before comparing/subtracting.
        # astimezone can push a boundary date past datetime's range —
        # OverflowError is not caught by pydantic, so guard it explicitly
        # (matches the stations/ingresses models and _parse_iso_range_naive_utc).
        try:
            if start.tzinfo is not None:
                start = start.astimezone(timezone.utc).replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.astimezone(timezone.utc).replace(tzinfo=None)
        except OverflowError:
            raise ValueError("start_date/end_date is out of the supported range.")
        # A date-only end_date means "through the end of that UTC day" — widen it
        # so a same-day date-only range isn't rejected (matches the stations /
        # ingresses models, the MCP _validate_iso_range helper, and the factory).
        if "T" not in self.end_date and "t" not in self.end_date and " " not in self.end_date:
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        if end <= start:
            raise ValueError("end_date must be after start_date.")
        # Cap the span to keep payloads bounded (~10 years of lunations).
        if (end - start).days > 3660:
            raise ValueError("Range too large; maximum span is ~10 years.")
        if self.phases is not None:
            allowed = {"new", "first_quarter", "full", "last_quarter"}
            invalid = [p for p in self.phases if p not in allowed]
            if invalid:
                raise ValueError(f"Invalid phase(s): {invalid}. Allowed: {sorted(allowed)}")
        return self


class RetrogradeStationsRequestModel(StrictRequestModel):
    """Request payload for finding planetary retrograde/direct stations."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-12-31'.",
    )
    planets: Optional[list[str]] = Field(
        default=None,
        description=("Optional subset of Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto. The Sun and Moon never station."),
    )

    @model_validator(mode="after")
    def validate_range(self) -> "RetrogradeStationsRequestModel":
        from datetime import datetime, timezone

        try:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError(f"start_date/end_date must be ISO dates: {exc}")
        try:
            if start.tzinfo is not None:
                start = start.astimezone(timezone.utc).replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.astimezone(timezone.utc).replace(tzinfo=None)
        except OverflowError:
            raise ValueError("start_date/end_date is out of the supported range.")
        # A date-only end_date means "through the end of that UTC day" (the
        # factory's semantics); compare against end-of-day, not midnight. Check
        # both T/t (fromisoformat accepts a lowercase 't') and a space separator.
        if "T" not in self.end_date and "t" not in self.end_date and " " not in self.end_date:
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        if end <= start:
            raise ValueError("end_date must be after start_date.")
        if (end - start).days > 3660:
            raise ValueError("Range too large; maximum span is ~10 years.")
        if self.planets is not None:
            allowed = {
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
            }
            invalid = [p for p in self.planets if p not in allowed]
            if invalid:
                raise ValueError(f"Invalid or non-stationing planet(s): {invalid}. Allowed: {sorted(allowed)}")
            # Deduplicate (preserve order): the factory scans the list as-is, so
            # duplicates would double the work and double every result.
            self.planets = list(dict.fromkeys(self.planets))
        return self


class SignIngressesRequestModel(StrictRequestModel):
    """Request payload for finding zodiac sign ingresses."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-12-31'.",
    )
    planets: Optional[list[str]] = Field(
        default=None,
        description=("Optional subset of Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Moon. Defaults to Sun..Pluto (Moon is opt-in)."),
    )

    @model_validator(mode="after")
    def validate_range(self) -> "SignIngressesRequestModel":
        from datetime import datetime, timezone

        try:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError(f"start_date/end_date must be ISO dates: {exc}")
        try:
            if start.tzinfo is not None:
                start = start.astimezone(timezone.utc).replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.astimezone(timezone.utc).replace(tzinfo=None)
        except OverflowError:
            raise ValueError("start_date/end_date is out of the supported range.")
        # A date-only end_date means "through the end of that UTC day" (the
        # factory's semantics); compare against end-of-day, not midnight. Check
        # both T/t (fromisoformat accepts a lowercase 't') and a space separator.
        if "T" not in self.end_date and "t" not in self.end_date and " " not in self.end_date:
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        if end <= start:
            raise ValueError("end_date must be after start_date.")
        if (end - start).days > 3660:
            raise ValueError("Range too large; maximum span is ~10 years.")
        if self.planets is not None:
            allowed = {
                "Sun",
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
                "Moon",
            }
            invalid = [p for p in self.planets if p not in allowed]
            if invalid:
                raise ValueError(f"Invalid planet(s): {invalid}. Allowed: {sorted(allowed)}")
            # Deduplicate (preserve order): the factory scans the list as-is, so
            # duplicates would double the work and double every result.
            self.planets = list(dict.fromkeys(self.planets))
        return self


class MundaneAspectsRequestModel(StrictRequestModel):
    """Request payload for the mundane aspectarian (exact transiting-to-transiting aspects)."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-31'.",
    )
    points: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional subset of bodies to scan (Moon, Mercury, Venus, Sun, Mars, Jupiter, "
            "Saturn, Chiron, Uranus, Neptune, Pluto, Mean_North_Lunar_Node, "
            "True_North_Lunar_Node). Defaults to Sun..Pluto — the Moon is opt-in "
            "(it alone perfects ~75 aspects/month)."
        ),
    )
    aspects: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional aspect names to search for. Defaults to the five Ptolemaic majors "
            "(conjunction, sextile, square, trine, opposition); the minor longitude aspects "
            "(semi-sextile, semi-square, quintile, sesquiquadrate, biquintile, quincunx) are accepted."
        ),
    )
    zodiac_type: ZodiacType = Field(
        default="Tropical",
        description="Zodiac for the reported longitudes/signs (aspect instants are zodiac-independent).",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )

    @model_validator(mode="after")
    def validate_range(self) -> "MundaneAspectsRequestModel":
        _validate_scan_range(self.start_date, self.end_date, 366, "~1 year")
        if self.points is not None:
            invalid = [p for p in self.points if p not in MUNDANE_ASPECT_POINTS]
            if invalid:
                raise ValueError(f"Invalid point(s): {invalid}. Allowed: {list(MUNDANE_ASPECT_POINTS)}")
            self.points = list(dict.fromkeys(self.points))
        if self.aspects is not None:
            invalid = [a for a in self.aspects if a not in MUNDANE_ASPECT_NAMES]
            if invalid:
                raise ValueError(f"Invalid aspect(s): {invalid}. Allowed: {list(MUNDANE_ASPECT_NAMES)}")
            self.aspects = list(dict.fromkeys(self.aspects))
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")
        return self


class SolarPhaseThresholdsRequestModel(StrictRequestModel):
    """Half-widths, in degrees, of the three solar-proximity bands.

    Declared here rather than reusing the engine's model so the request schema
    stays a pure API surface: the values are converted to the engine's own
    ``SolarPhaseThresholdsModel`` at the call site, and only when the caller
    actually sent them.
    """

    model_config = {"extra": "forbid"}

    cazimi_deg: float = Field(default=0.2833, gt=0, le=90, description="Half-width of cazimi, in degrees (default 0.2833° = 17 arcminutes).")
    combust_deg: float = Field(default=8.5, gt=0, le=90, description="Half-width of combustion, in degrees (default 8.5° = 8°30').")
    under_beams_deg: float = Field(default=17.0, gt=0, le=90, description="Half-width of the Sun's beams, in degrees (default 17°).")

    @model_validator(mode="after")
    def validate_band_ordering(self) -> "SolarPhaseThresholdsRequestModel":
        if not (self.cazimi_deg < self.combust_deg < self.under_beams_deg):
            raise ValueError("Solar phase thresholds must widen outward: cazimi_deg < combust_deg < under_beams_deg.")
        return self


class PlanetaryPhenomenaRequestModel(StrictRequestModel):
    """Request payload for computing planetary observational phenomena."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject defining the moment for phenomena calculation.")
    planets: Optional[list[str]] = Field(
        default=None,
        description="Planets to compute phenomena for. Defaults to all planets if omitted.",
    )
    solar_phase_thresholds: Optional[SolarPhaseThresholdsRequestModel] = Field(
        default=None,
        description=(
            "Override the band half-widths that classify each planet's `solar_phase` (cazimi / combust / under_the_beams / free). Omit to use the traditional defaults, which the response echoes back."
        ),
    )


HELIACAL_MAX_EVENT_WORK = 40


MAX_HELIACAL_PLANETS = 12


class HeliacalEventsRequestModel(StrictRequestModel):
    """Request payload for searching heliacal rising/setting events."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject defining the starting moment and observation location.")
    count: int = Field(
        default=5,
        description="Number of heliacal events to return.",
        ge=1,
        le=20,
    )
    planets: Optional[list[str]] = Field(
        default=None,
        description="Planet or star names to search events for.",
        max_length=MAX_HELIACAL_PLANETS,
    )
    event_types: Optional[list[Literal["heliacal_rising", "heliacal_setting", "evening_first", "morning_last"]]] = Field(
        default=None,
        description=("Heliacal event types to search for. Defaults to ['heliacal_rising', 'heliacal_setting']. 'evening_first' and 'morning_last' apply only to the inner planets (Mercury, Venus)."),
        examples=[["heliacal_rising", "heliacal_setting"]],
    )

    @model_validator(mode="after")
    def validate_heliacal_work(self) -> "HeliacalEventsRequestModel":
        # event_types defaults to the two-element set when omitted.
        n_types = len(self.event_types) if self.event_types else 2
        work = self.count * n_types
        if work > HELIACAL_MAX_EVENT_WORK:
            raise ValueError(f"Heliacal search costs {work} event-type units (count × event_types; max {HELIACAL_MAX_EVENT_WORK}). Reduce count or event_types.")
        return self


class OccultationSearchRequestModel(StrictRequestModel):
    """Request payload for searching stellar occultations."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject defining the starting moment and observation location.")
    planet: Literal["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"] = Field(
        default="Venus",
        description="Occulted body — the planet the Moon passes in front of (e.g. 'Venus').",
    )
    count: int = Field(
        default=5,
        description="Number of occultation events to return.",
        ge=1,
        le=50,
    )
