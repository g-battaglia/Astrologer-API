"""Pydantic input models for MCP tools.

These models generate rich JSON schemas that MCP clients can use for
discoverability and validation.  They are intentionally separate from
the REST ``request_models`` — MCP models use ``extra="ignore"`` for
LLM-friendly tolerance, while REST models use ``extra="forbid"`` for
strict API contracts.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..types.request_models import DEFAULT_NAKSHATRA_AYANAMSA


class MCPSubjectInput(BaseModel):
    """Astrological subject birth data.

    Required: name, year, month, day, hour, minute, city.
    Location: provide (latitude + longitude + timezone) for offline mode,
    OR geonames_username for online geocoding.
    See astrologer://docs/subject-model for the full reference.
    """

    model_config = ConfigDict(extra="ignore")

    # --- Required fields ---
    name: str = Field(description="Display name for the subject.")
    year: int = Field(
        description="Birth year in astronomical numbering (0 = 1 BCE, -1 = 2 BCE).",
        ge=-13200,
        le=9999,
    )
    month: int = Field(description="Birth month (1-12).", ge=1, le=12)
    day: int = Field(description="Birth day (1-31).", ge=1, le=31)
    hour: int = Field(description="Birth hour (0-23).", ge=0, le=23)
    minute: int = Field(description="Birth minute (0-59).", ge=0, le=59)
    city: str = Field(description="City name.")

    # --- Optional fields with defaults ---
    nation: str = Field(
        default="GB",
        description="ISO 3166-1 alpha-2 country code (e.g. 'IT', 'US', 'GB').",
    )
    second: int = Field(default=0, description="Birth second (0-59).", ge=0, le=59)

    # --- Location (offline mode) ---
    latitude: Optional[float] = Field(default=None, description="Latitude (-90 to 90).", ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, description="Longitude (-180 to 180).", ge=-180, le=180)
    timezone: Optional[str] = Field(default=None, description="IANA timezone (e.g. 'Europe/Rome', 'America/New_York').")

    # --- Location (online mode) ---
    geonames_username: Optional[str] = Field(default=None, description="GeoNames username for online geocoding (omit latitude/longitude/timezone).")

    # --- Astrological configuration ---
    zodiac_type: str = Field(default="Tropical", description="'Tropical' or 'Sidereal'.")
    sidereal_mode: Optional[str] = Field(default=None, description="Sidereal ayanamsha (required when zodiac_type='Sidereal').")
    houses_system_identifier: str = Field(default="P", description="House system identifier (e.g. 'P'=Placidus, 'W'=Whole Sign, 'K'=Koch).")
    perspective_type: str = Field(
        default="Apparent Geocentric",
        description="Astronomical perspective: 'Apparent Geocentric', 'True Geocentric', or 'Heliocentric'.",
    )
    custom_ayanamsa_t0: Optional[float] = Field(default=None, description="Reference epoch (Julian Day) for USER sidereal mode.")
    custom_ayanamsa_ayan_t0: Optional[float] = Field(default=None, description="Ayanamsa offset in degrees at the reference epoch.")

    # --- Extra location ---
    altitude: Optional[float] = Field(default=None, description="Altitude above sea level in meters.")
    is_dst: Optional[bool] = Field(default=None, description="Override automatic DST detection.")

    # --- v6 calculation flags ---
    calculate_dignities: bool = Field(
        default=False,
        description="Compute essential dignities and Chaldean decans / Egyptian terms.",
    )
    calculate_nakshatra: bool = Field(
        default=False,
        description="Compute Vedic Nakshatra, pada, and Vimsottari Dasha lord.",
    )
    nakshatra_ayanamsa: Optional[str] = Field(
        default=DEFAULT_NAKSHATRA_AYANAMSA,
        description=(
            "Ayanamsa used to place the nakshatras on a non-sidereal chart. The nakshatras are a sidereal grid, "
            "so on a Tropical chart their longitudes must be corrected by an ayanamsa before the mansion is read "
            f"(default '{DEFAULT_NAKSHATRA_AYANAMSA}'). Ignored when the chart is already Sidereal — there the chart's own "
            "`sidereal_mode` governs, and the echoed value is null. Set to null for the uncorrected legacy values "
            "(tropical longitudes read straight onto the nakshatra grid)."
        ),
    )
    calculate_gauquelin: bool = Field(
        default=False,
        description="Compute Gauquelin sector position (1-36) for each point.",
    )
    calculate_nutation: bool = Field(
        default=False,
        description="Compute nutation and obliquity parameters.",
    )
    calculate_local_space: bool = Field(
        default=False,
        description="Compute azimuth and altitude above horizon for each point.",
    )
    active_fixed_stars: Optional[list[str]] = Field(
        default=None,
        description="Additional fixed star names to calculate (e.g. ['Rigel', 'Sirius', 'Vega']).",
    )
    active_midpoints: Optional[list[str]] = Field(
        default=None,
        description=(
            "Midpoint pair identifiers ('<name_a>_<name_b>') to materialize as sensitive points on "
            "the chart wheel, e.g. ['Sun_Moon', 'Sun_Mercury']. Format mirrors the natal point names. "
            "Unknown pairs are silently skipped."
        ),
        max_length=100,
    )


class MCPReturnLocationInput(BaseModel):
    """Location override for planetary return charts.

    Provide (latitude + longitude + timezone) for offline mode,
    OR geonames_username for online geocoding.
    If omitted entirely, the natal subject's location is used.
    """

    model_config = ConfigDict(extra="ignore")

    city: Optional[str] = Field(default=None, description="City name for the return location.")
    nation: Optional[str] = Field(default=None, description="ISO 3166-1 alpha-2 country code.")
    latitude: Optional[float] = Field(default=None, description="Latitude (-90 to 90).", ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, description="Longitude (-180 to 180).", ge=-180, le=180)
    timezone: Optional[str] = Field(default=None, description="IANA timezone identifier.")
    altitude: Optional[float] = Field(default=None, description="Altitude above sea level in meters.")
    geonames_username: Optional[str] = Field(default=None, description="GeoNames username for online geocoding.")


class MCPSolarPhaseThresholdsInput(BaseModel):
    """Half-widths, in degrees, of the three solar-proximity bands.

    Mirrors the REST ``SolarPhaseThresholdsRequestModel`` — same defaults, same
    "must widen outward" rule — so a caller reading either surface gets the same
    answer. Kept as a separate declaration for the same reason the REST one is:
    the values are converted to the engine's ``SolarPhaseThresholdsModel`` at
    the call site, and only when the caller actually sent them.
    """

    model_config = ConfigDict(extra="ignore")

    cazimi_deg: float = Field(default=0.2833, gt=0, le=90, description="Half-width of cazimi, in degrees (default 0.2833° = 17 arcminutes).")
    combust_deg: float = Field(default=8.5, gt=0, le=90, description="Half-width of combustion, in degrees (default 8.5° = 8°30').")
    under_beams_deg: float = Field(default=17.0, gt=0, le=90, description="Half-width of the Sun's beams, in degrees (default 17°).")

    @model_validator(mode="after")
    def validate_band_ordering(self) -> "MCPSolarPhaseThresholdsInput":
        if not (self.cazimi_deg < self.combust_deg < self.under_beams_deg):
            raise ValueError("Solar phase thresholds must widen outward: cazimi_deg < combust_deg < under_beams_deg.")
        return self
