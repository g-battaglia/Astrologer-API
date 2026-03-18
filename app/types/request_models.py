from __future__ import annotations

from abc import ABC
from logging import getLogger
from typing import Literal, Mapping, Optional, Union, get_args

from pydantic import BaseModel, Field, field_validator, model_validator
from pytz import all_timezones

from kerykeion.schemas import (
    ActiveAspect,
    AxialCusps,
    HousesSystemIdentifier,
    KerykeionChartLanguage,
    KerykeionChartStyle,
    KerykeionChartTheme,
    PerspectiveType,
    Planet,
    SiderealMode,
    ZodiacType,
)
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_ASPECTS,
    DEFAULT_ACTIVE_POINTS,
)

logger = getLogger(__name__)

# ---------------------------------------------------------------------------
# Active Points Normalization
# ---------------------------------------------------------------------------
# Pre-computed lookup tables for case-insensitive point name normalization.
# Built once at module load for O(1) lookups per point.

_POINT_LOWER_TO_CANONICAL: dict[str, str] = {p.lower(): p for p in get_args(Planet)}

_POINT_ALIASES: dict[str, str] = {
    "mean_node": "Mean_North_Lunar_Node",
    "true_node": "True_North_Lunar_Node",
    "north_node": "Mean_North_Lunar_Node",
    "south_node": "Mean_South_Lunar_Node",
    "mean_south_node": "Mean_South_Lunar_Node",
    "true_south_node": "True_South_Lunar_Node",
    "mc": "Medium_Coeli",
    "ic": "Imum_Coeli",
    "asc": "Ascendant",
    "desc": "Descendant",
    "lilith": "Mean_Lilith",
}


def _normalize_point_name(name: str) -> str:
    """Normalize a point name to canonical format.

    Examples:
        'chiron' -> 'Chiron'
        'MERCURY' -> 'Mercury'
        'mean_node' -> 'Mean_North_Lunar_Node'
    """
    lower = name.lower()
    return _POINT_ALIASES.get(lower) or _POINT_LOWER_TO_CANONICAL.get(lower) or name


def _normalize_active_points(value: Optional[list]) -> Optional[list]:
    """Normalize a list of point names. Used by Pydantic validators."""
    if value is None:
        return None
    return [_normalize_point_name(p) if isinstance(p, str) else p for p in value]


# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

DistributionMethod = Literal["weighted", "pure_count"]


class AbstractBaseSubjectModel(BaseModel, ABC):
    """Shared subject fields used across requests."""

    model_config = {"extra": "forbid"}

    year: int = Field(
        description="Year component of the event. Supports historical dates from 1 CE to 3000 CE.",
        ge=1,
        le=3000,
        examples=[1980],
    )
    month: int = Field(description="Month component of the event.", ge=1, le=12, examples=[12])
    day: int = Field(description="Day component of the event.", ge=1, le=31, examples=[12])
    hour: int = Field(description="Hour component of the event (0-23).", ge=0, le=23, examples=[12])
    minute: int = Field(description="Minute component of the event (0-59).", ge=0, le=59, examples=[12])
    second: Optional[int] = Field(
        default=0,
        description="Seconds component of the event (0-59).",
        ge=0,
        le=59,
        examples=[0],
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude of the location (-180 to 180).",
        ge=-180,
        le=180,
        examples=[0.0],
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude of the location (-90 to 90).",
        ge=-90,
        le=90,
        examples=[51.4825766],
    )
    altitude: Optional[float] = Field(
        default=None,
        description="Altitude above sea level in meters.",
        examples=[35.0],
    )
    city: str = Field(description="City name associated with the event.", examples=["London"])
    nation: Optional[str] = Field(
        default=None,
        description="Two-letter ISO 3166-1 alpha-2 nation code.",
        examples=["GB"],
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone identifier for the event.",
        examples=["Europe/London"],
    )
    is_dst: Optional[bool] = Field(
        default=None,
        description="Override automatic daylight saving time detection.",
    )
    geonames_username: Optional[str] = Field(
        default=None,
        description="Geonames username used to resolve location data when GPS coordinates are not provided.",
        examples=[None],
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in all_timezones:
            raise ValueError(f"Invalid timezone '{value}'. Please use a valid timezone from the IANA database.")
        return value

    @field_validator("nation")
    @classmethod
    def validate_nation(cls, value: Optional[str]) -> str:
        if not value or value.lower() == "null":
            return "null"
        if len(value) != 2 or not value.isalpha():
            raise ValueError(
                f"Invalid nation code: '{value}'. It must be a 2-letter country code (ISO 3166-1 alpha-2)."
            )
        return value.upper()

    @model_validator(mode="after")
    def ensure_location_source(self) -> "AbstractBaseSubjectModel":
        lat = self.latitude
        lng = self.longitude
        tz = self.timezone
        geonames = self.geonames_username

        missing_coordinates = sum(field is None for field in (lat, lng, tz))

        if missing_coordinates == 3 and not geonames:
            raise ValueError("Provide latitude, longitude, timezone or specify geonames_username.")

        if 0 < missing_coordinates < 3 and not geonames:
            raise ValueError("Provide all location fields (latitude, longitude, timezone) or geonames_username.")

        if geonames and (lat is not None or lng is not None or tz is not None):
            self.latitude = None
            self.longitude = None
            self.timezone = None

        return self


class SubjectModel(AbstractBaseSubjectModel):
    """Subject definition used across most endpoints."""

    model_config = {"extra": "forbid"}

    name: str = Field(description="Display name for the subject.", examples=["John Doe"])
    zodiac_type: Optional[ZodiacType] = Field(
        default="Tropical",
        description="Zodiac type used for the calculation.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )
    perspective_type: Optional[PerspectiveType] = Field(
        default="Apparent Geocentric",
        description="Astronomical perspective used for the calculation.",
        examples=list(get_args(PerspectiveType)),
    )
    houses_system_identifier: Optional[HousesSystemIdentifier] = Field(
        default="P",
        description="Identifier for the house system.",
        examples=list(get_args(HousesSystemIdentifier)),
    )
    custom_ayanamsa_t0: Optional[float] = Field(
        default=None,
        description="Reference epoch as Julian Day for the USER sidereal mode. Required when sidereal_mode='USER'.",
        examples=[2451545.0],
    )
    custom_ayanamsa_ayan_t0: Optional[float] = Field(
        default=None,
        description="Ayanamsa offset in degrees at the reference epoch. Required when sidereal_mode='USER'.",
        examples=[23.5],
    )

    @field_validator("zodiac_type")
    @classmethod
    def validate_zodiac_type(cls, value: Optional[ZodiacType], info) -> Optional[ZodiacType]:
        sidereal_mode = info.data.get("sidereal_mode")
        if sidereal_mode and value != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        return value

    @field_validator("sidereal_mode")
    @classmethod
    def validate_sidereal_mode(cls, value: Optional[SiderealMode], info) -> Optional[SiderealMode]:
        zodiac_type = info.data.get("zodiac_type")
        if value and zodiac_type != "Sidereal":
            raise ValueError("sidereal_mode requires zodiac_type='Sidereal'.")
        return value

    @model_validator(mode="after")
    def validate_custom_ayanamsa(self) -> "SubjectModel":
        if self.sidereal_mode == "USER":
            if self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None:
                raise ValueError(
                    "custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are required when sidereal_mode='USER'."
                )
        return self

    @field_validator("perspective_type", mode="before")
    @classmethod
    def default_perspective_type(cls, value: Optional[PerspectiveType]) -> PerspectiveType:
        return value or "Apparent Geocentric"

    @field_validator("houses_system_identifier", mode="before")
    @classmethod
    def default_house_system(cls, value: Optional[HousesSystemIdentifier]) -> HousesSystemIdentifier:
        return value or "P"


class TransitSubjectModel(AbstractBaseSubjectModel):
    """Transit subject definition; inherits base validators."""

    model_config = {"extra": "forbid"}

    name: Optional[str] = Field(default="Transit", description="Label used for the transit subject.")


class ChartDataConfigurationMixin(BaseModel):
    """Mixin holding computation options for chart data (no rendering)."""

    model_config = {"extra": "forbid"}

    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(
        default=None,
        description="Override the active points used for calculations.",
        examples=[DEFAULT_ACTIVE_POINTS],
    )
    active_aspects: Optional[list[ActiveAspect]] = Field(
        default=None,
        description="Override the active aspects and their orbs.",
        examples=[DEFAULT_ACTIVE_ASPECTS],
    )
    distribution_method: DistributionMethod = Field(
        default="weighted",
        description="Element/quality distribution strategy.",
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Normalize point names to canonical format, accepting case-insensitive and aliased inputs."""
        return _normalize_active_points(value)

    custom_distribution_weights: Optional[Mapping[str, float]] = Field(
        default=None,
        description="Custom weights used when distribution_method='weighted'.",
        examples=[
            {
                "sun": 2.0,
                "moon": 2.0,
                "ascendant": 2.0,
                "medium_coeli": 1.5,
                "mercury": 1.5,
                "venus": 1.5,
                "mars": 1.5,
                "jupiter": 1.0,
                "saturn": 1.0,
            }
        ],
    )


class ChartRenderingMixin(ChartDataConfigurationMixin):
    """Mixin adding chart rendering options (theme, language, split_chart, transparent background, runtime ChartDrawer tweaks)."""

    model_config = {"extra": "forbid"}

    theme: Optional[KerykeionChartTheme] = Field(
        default="classic",
        description="Visual theme for the generated SVG chart.",
        examples=list(get_args(KerykeionChartTheme)),
    )
    language: Optional[KerykeionChartLanguage] = Field(
        default="EN",
        description="Language used for chart labels.",
        examples=list(get_args(KerykeionChartLanguage)),
    )
    split_chart: bool = Field(
        default=False,
        description="Return wheel and aspect grid as separate SVG strings in 'chart_wheel' and 'chart_grid' keys.",
    )
    transparent_background: bool = Field(
        default=False,
        description="Render chart with transparent background instead of theme default.",
    )
    show_house_position_comparison: bool = Field(
        default=True,
        description="Display the house comparison table next to the chart wheel.",
    )
    show_cusp_position_comparison: bool = Field(
        default=True,
        description="Display the cusp position comparison table next to the chart wheel (for dual charts).",
    )
    show_degree_indicators: bool = Field(
        default=True,
        description="Display radial lines and degree numbers for planet positions on the chart wheel.",
    )
    show_aspect_icons: bool = Field(
        default=True,
        description="Display aspect icons on the chart wheel aspect lines.",
    )
    custom_title: Optional[str] = Field(
        default=None,
        description="Temporarily override the rendered chart title (max 40 characters).",
        max_length=40,
        examples=["Custom Chart Title"],
    )
    style: KerykeionChartStyle = Field(
        default="classic",
        description="Chart rendering style: 'classic' (traditional wheel) or 'modern' (concentric rings).",
        examples=list(get_args(KerykeionChartStyle)),
    )
    show_zodiac_background_ring: bool = Field(
        default=True,
        description="Show colored zodiac sign wedges on the wheel. Only affects 'modern' style.",
    )
    double_chart_aspect_grid_type: Literal["list", "table"] = Field(
        default="list",
        description="Layout for double-chart aspect display: 'list' (vertical) or 'table' (grid matrix).",
    )

    @field_validator("custom_title")
    @classmethod
    def normalize_custom_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class BirthChartRequestModel(ChartRenderingMixin):
    """Request payload for the birth chart endpoint (with SVG rendering)."""

    subject: SubjectModel = Field(description="Subject used for the birth chart calculation.")


class BirthChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the birth chart data endpoint (data only, no SVG)."""

    subject: SubjectModel = Field(description="Subject used for the birth chart calculation.")


class SynastryChartRequestModel(ChartRenderingMixin):
    """Request payload for the synastry chart endpoint (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Primary subject (inner wheel).")
    second_subject: SubjectModel = Field(description="Secondary subject (outer wheel).")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )
    include_relationship_score: bool = Field(
        default=True,
        description="Include relationship score analysis in the computed data.",
    )


class SynastryChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the synastry chart data endpoint (data only, no SVG)."""

    first_subject: SubjectModel = Field(description="Primary subject (inner wheel).")
    second_subject: SubjectModel = Field(description="Secondary subject (outer wheel).")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )
    include_relationship_score: bool = Field(
        default=True,
        description="Include relationship score analysis in the computed data.",
    )


class TransitChartRequestModel(ChartRenderingMixin):
    """Request payload for the transit chart endpoint (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Natal subject used for the transit calculation.")
    transit_subject: TransitSubjectModel = Field(description="Transit moment data.")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )


class TransitChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the transit chart data endpoint (data only, no SVG)."""

    first_subject: SubjectModel = Field(description="Natal subject used for the transit calculation.")
    transit_subject: TransitSubjectModel = Field(description="Transit moment data.")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )


class NowSubjectDefinitionModel(BaseModel):
    """Configuration for the 'now' subject (name, zodiac, etc.)."""

    model_config = {"extra": "forbid"}

    name: str = Field(default="Now", description="Display name for the subject.")
    zodiac_type: Optional[ZodiacType] = Field(
        default="Tropical",
        description="Zodiac type used for the calculation.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )
    perspective_type: Optional[PerspectiveType] = Field(
        default="Apparent Geocentric",
        description="Astronomical perspective used for the calculation.",
        examples=list(get_args(PerspectiveType)),
    )
    houses_system_identifier: Optional[HousesSystemIdentifier] = Field(
        default="P",
        description="Identifier for the house system.",
        examples=list(get_args(HousesSystemIdentifier)),
    )

    @model_validator(mode="after")
    def validate_zodiac_configuration(self) -> "NowSubjectDefinitionModel":
        zodiac_type = self.zodiac_type
        sidereal_mode = self.sidereal_mode

        if sidereal_mode and zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")

        if zodiac_type == "Sidereal" and not sidereal_mode:
            # Optional: enforce sidereal_mode if zodiac_type is Sidereal,
            # or let it default if the backend handles it.
            # The original validator said: "sidereal_mode requires zodiac_type='Sidereal'"
            # which implies the reverse check.
            pass

        return self

    @field_validator("perspective_type", mode="before")
    @classmethod
    def default_perspective_type(cls, value: Optional[PerspectiveType]) -> PerspectiveType:
        return value or "Apparent Geocentric"

    @field_validator("houses_system_identifier", mode="before")
    @classmethod
    def default_house_system(cls, value: Optional[HousesSystemIdentifier]) -> HousesSystemIdentifier:
        return value or "P"


class NowChartRequestModel(NowSubjectDefinitionModel, ChartRenderingMixin):
    """Request payload for the 'now' chart endpoint (with SVG rendering)."""

    pass


class NowSubjectRequestModel(NowSubjectDefinitionModel):
    """Request payload for the 'now' subject endpoint."""

    pass


class BirthDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for retrieving subject data without charts."""

    subject: SubjectModel = Field(description="Subject used for the birth data calculation.")


class CompositeChartRequestModel(ChartRenderingMixin):
    """Request payload for composite chart calculations (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Primary subject used for the composite chart.")
    second_subject: SubjectModel = Field(description="Secondary subject used for the composite chart.")


class CompositeChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for composite chart data calculations (data only, no SVG)."""

    first_subject: SubjectModel = Field(description="Primary subject used for the composite chart.")
    second_subject: SubjectModel = Field(description="Secondary subject used for the composite chart.")


class ReturnLocationModel(BaseModel):
    """Optional location override for planetary return calculations."""

    model_config = {"extra": "forbid"}

    city: Optional[str] = Field(default=None, description="Target city for the return chart.")
    nation: Optional[str] = Field(
        default=None,
        description="Two-letter ISO nation code.",
        examples=["GB"],
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude of the target location.",
        ge=-180,
        le=180,
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude of the target location.",
        ge=-90,
        le=90,
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Timezone of the target location.",
        examples=["Europe/London"],
    )
    altitude: Optional[float] = Field(
        default=None,
        description="Altitude in meters for the target location.",
    )
    geonames_username: Optional[str] = Field(
        default=None,
        description="Geonames username to resolve the provided city when coordinates are missing.",
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in all_timezones:
            raise ValueError(f"Invalid timezone '{value}'. Please use a valid timezone from the IANA database.")
        return value

    @field_validator("nation")
    @classmethod
    def validate_nation(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value) != 2 or not value.isalpha():
            raise ValueError(
                f"Invalid nation code: '{value}'. It must be a 2-letter country code (ISO 3166-1 alpha-2)."
            )
        return value.upper()

    @model_validator(mode="after")
    def ensure_location_source(self) -> "ReturnLocationModel":
        lat = self.latitude
        lng = self.longitude
        tz = self.timezone
        geonames = self.geonames_username

        missing_coordinates = sum(field is None for field in (lat, lng, tz))

        if missing_coordinates == 3 and not geonames and not (self.city and self.nation):
            raise ValueError("Provide latitude, longitude, timezone, or supply geonames_username with city and nation.")

        if 0 < missing_coordinates < 3 and not geonames:
            raise ValueError("Provide all location fields (latitude, longitude, timezone) or geonames_username.")

        # If complete coordinates are provided, they take priority; clear geonames_username
        if missing_coordinates == 0 and geonames:
            logger.info(
                "Complete coordinates provided (lat=%.4f, lng=%.4f, tz=%s), ignoring geonames_username '%s'",
                lat,
                lng,
                tz,
                geonames,
            )
            self.geonames_username = None

        return self


class PlanetaryReturnRequestModel(ChartRenderingMixin):
    """Shared payload for solar and lunar return endpoints (with SVG rendering)."""

    subject: SubjectModel = Field(description="Natal subject used for the return calculation.")
    year: Optional[int] = Field(
        default=None,
        description="Calendar year to search for the next return.",
        ge=1,
        le=3000,
    )
    month: Optional[int] = Field(
        default=None,
        description="Optional month (1-12) to start the search from. Used with year and day.",
        ge=1,
        le=12,
    )
    day: Optional[int] = Field(
        default=1,
        description="Optional day (1-31) to start the search from. Requires month and year.",
        ge=1,
        le=31,
    )
    iso_datetime: Optional[str] = Field(
        default=None,
        description="ISO formatted datetime used as starting point for the search.",
        examples=["2025-05-01T00:00:00+00:00"],
    )
    wheel_type: Literal["dual", "single"] = Field(
        default="dual",
        description="Return chart configuration: 'dual' wheel (natal + return) or 'single' wheel.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison for dual wheel returns.",
    )
    return_location: Optional[ReturnLocationModel] = Field(
        default=None,
        description="Override location used for the return chart.",
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "PlanetaryReturnRequestModel":
        if not any([self.year, self.iso_datetime]):
            raise ValueError(
                "Provide either 'iso_datetime' or 'year' (with optional month and day) to locate the return."
            )

        if self.month and not self.year:
            raise ValueError("Month can only be provided together with a year.")

        if self.day and self.day != 1 and not self.month:
            raise ValueError("Day can only be provided together with month and year.")

        if self.wheel_type == "single":
            self.include_house_comparison = False

        return self


class MoonPhaseRequestModel(BaseModel):
    """Request payload for moon phase details at a specific date/time and location."""

    model_config = {"extra": "forbid"}

    year: int = Field(description="Year of the event.", ge=1, le=3000, examples=[1993])
    month: int = Field(description="Month of the event.", ge=1, le=12, examples=[10])
    day: int = Field(description="Day of the event.", ge=1, le=31, examples=[10])
    hour: int = Field(description="Hour of the event (0-23).", ge=0, le=23, examples=[12])
    minute: int = Field(description="Minute of the event (0-59).", ge=0, le=59, examples=[12])
    second: int = Field(
        default=0,
        description="Seconds of the event (0-59).",
        ge=0,
        le=59,
        examples=[0],
    )
    latitude: float = Field(
        description="Latitude of the location (-90 to 90).",
        ge=-90,
        le=90,
        examples=[51.5074],
    )
    longitude: float = Field(
        description="Longitude of the location (-180 to 180).",
        ge=-180,
        le=180,
        examples=[-0.1276],
    )
    timezone: str = Field(
        description="IANA timezone identifier for the event.",
        examples=["Europe/London"],
    )
    using_default_location: bool = Field(
        default=False,
        description="Flag indicating whether the location is a default fallback.",
    )
    location_precision: int = Field(
        default=0,
        description="Number of decimal places used to round latitude and longitude in the response.",
        ge=0,
        le=10,
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        if value not in all_timezones:
            raise ValueError(f"Invalid timezone '{value}'. Please use a valid timezone from the IANA database.")
        return value


class NowMoonPhaseRequestModel(BaseModel):
    """Request payload for the 'now' moon phase endpoint. All fields are optional."""

    model_config = {"extra": "forbid"}

    using_default_location: bool = Field(
        default=True,
        description="Flag indicating whether the location is a default fallback.",
    )
    location_precision: int = Field(
        default=0,
        description="Number of decimal places used to round latitude and longitude in the response.",
        ge=0,
        le=10,
    )


class PlanetaryReturnDataRequestModel(ChartDataConfigurationMixin):
    """Shared payload for solar and lunar return data endpoints (data only, no SVG)."""

    subject: SubjectModel = Field(description="Natal subject used for the return calculation.")
    year: Optional[int] = Field(
        default=None,
        description="Calendar year to search for the next return.",
        ge=1,
        le=3000,
    )
    month: Optional[int] = Field(
        default=None,
        description="Optional month (1-12) to start the search from. Used with year and day.",
        ge=1,
        le=12,
    )
    day: Optional[int] = Field(
        default=1,
        description="Optional day (1-31) to start the search from. Requires month and year.",
        ge=1,
        le=31,
    )
    iso_datetime: Optional[str] = Field(
        default=None,
        description="ISO formatted datetime used as starting point for the search.",
        examples=["2025-05-01T00:00:00+00:00"],
    )
    wheel_type: Literal["dual", "single"] = Field(
        default="dual",
        description="Return chart configuration: 'dual' wheel (natal + return) or 'single' wheel.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison for dual wheel returns.",
    )
    return_location: Optional[ReturnLocationModel] = Field(
        default=None,
        description="Override location used for the return chart.",
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "PlanetaryReturnDataRequestModel":
        if not any([self.year, self.iso_datetime]):
            raise ValueError(
                "Provide either 'iso_datetime' or 'year' (with optional month and day) to locate the return."
            )

        if self.month and not self.year:
            raise ValueError("Month can only be provided together with a year.")

        if self.day and self.day != 1 and not self.month:
            raise ValueError("Day can only be provided together with month and year.")

        if self.wheel_type == "single":
            self.include_house_comparison = False

        return self
