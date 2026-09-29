"""Predictive request models."""

from __future__ import annotations
from typing import Literal, Mapping, Optional, get_args
from pydantic import Field, field_validator, model_validator
from kerykeion.schemas import (
    KerykeionChartStyle,
    KerykeionChartTheme,
    KerykeionGlyphSize,
)
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy
from ..request_core import DistributionMethod, PointOrbAdjustmentValue, StrictRequestModel, SubjectModel, _check_point_orb_adjustments_capability, _normalize_active_points


class PrimaryDirectionsRequestModel(StrictRequestModel):
    """Request payload for computing primary directions (Placidus semi-arc)."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject for primary directions calculation.")
    max_years: float = Field(
        default=100,
        description="Maximum number of years to project directions forward.",
        ge=1,
        le=200,
    )
    rate_key: Literal["ptolemy", "naibod"] = Field(
        default="ptolemy",
        description="Direction rate: 'ptolemy' (1 degree RA = 1 year) or 'naibod' (59'08\" = 1 year).",
    )
    aspects: Optional[list[str]] = Field(
        default=None,
        description="Aspects to calculate (e.g. ['conjunction', 'opposition', 'trine']). Defaults to all.",
    )


class SecondaryProgressionsRequestModel(StrictRequestModel):
    """Request payload for computing the secondary-progressed chart."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject to progress.")
    target_iso_utc_datetime: Optional[str] = Field(
        default=None,
        description=("ISO-8601 UTC timestamp of the target moment (e.g. '2026-04-25T00:00:00Z'). Mutually exclusive with target_year."),
    )
    target_year: Optional[int] = Field(
        default=None,
        description=("Convenience: target year (Jan 1 at 00:00 UTC). Mutually exclusive with target_iso_utc_datetime."),
        ge=-13200,
        le=9999,
    )
    active_points: Optional[list[str]] = Field(
        default=None,
        description="Points to include in cross-aspect detection. Defaults to the standard predictive set.",
    )
    compute_aspects: bool = Field(
        default=True,
        description="If false, skip progressed-to-natal aspect detection.",
    )
    aspect_orb: float = Field(
        default=3.0,
        description="Orb in degrees for progressed-to-natal aspect detection (Astro-Seek default: 3°).",
        ge=0.1,
        le=10.0,
    )
    aspects: Optional[list[str]] = Field(
        default=None,
        description="Aspect names to detect. Defaults to 5 Ptolemaic (conjunction, opposition, trine, sextile, square).",
    )
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustmentValue]] = Field(
        default=None,
        description="Per-point orb adjustment table (point name → degrees added to the aspect base orb). When omitted, no adjustment applies — progressions use a flat, tight orb. An entry can also be an object of aspect name → degrees with '*' as the default for aspects not listed.",
        examples=[{"Sun": 1.5, "Moon": 1.5}, {"Sun": {"*": 1.5, "conjunction": 3.0}}],
    )

    @field_validator("point_orb_adjustments")
    @classmethod
    def _check_point_orb_capability(cls, value):
        return _check_point_orb_adjustments_capability(value)

    point_orb_adjustment_strategy: OrbAdjustmentStrategy = Field(
        default="max_explicit",
        description="How to combine the two points' orb adjustments when a table is supplied.",
    )
    axis_orb_limit: Optional[float] = Field(
        default=None,
        description="Override the maximum orb (in degrees) for aspects involving axial points (ASC, MC, DSC, IC).",
        ge=0,
        le=30,
    )
    distribution_method: DistributionMethod = Field(
        default="weighted",
        description="Element/quality distribution strategy for the progressed chart.",
    )
    custom_distribution_weights: Optional[Mapping[str, float]] = Field(
        default=None,
        description="Custom weights used when distribution_method='weighted'.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include the progressed-to-natal house overlay comparison.",
    )
    theme: Optional[KerykeionChartTheme] = Field(
        default="classic",
        description="Visual theme for the generated SVG chart.",
    )
    style: KerykeionChartStyle = Field(
        default="classic",
        description="Chart rendering style: 'classic' (traditional wheel) or 'modern' (concentric rings).",
        examples=list(get_args(KerykeionChartStyle)),
    )
    glyph_size: KerykeionGlyphSize = Field(
        default="medium",
        description=(
            "Size of the planet cluster on the wheel: 'small', 'medium' (default) or 'large' "
            "(the planet glyph at the classic style's own size, "
            "in the default configuration — zodiac background ring active). "
            "Only affects 'modern' style \u2014 the classic wheel draws a fixed-size glyph."
        ),
        examples=list(get_args(KerykeionGlyphSize)),
    )
    show_zodiac_background_ring: bool = Field(
        default=True,
        description="Draw the outer colored zodiac ring. Only affects 'modern' style.",
    )
    transparent_background: bool = Field(
        default=False,
        description="Render chart with transparent background instead of theme default.",
    )
    show_motion_state: bool = Field(
        default=False,
        description="Label stationary planets on the wheel: 'SR' when turning retrograde, 'SD' when turning direct.",
    )
    show_out_of_bounds: bool = Field(
        default=False,
        description="Badge points whose declination is beyond the Sun's extremes (about ±23°26') with 'OOB'.",
    )
    show_aspect_movement: bool = Field(
        default=False,
        description="Dash the aspect lines of separating aspects; applying aspects stay solid.",
    )
    show_relationship_score: bool = Field(
        default=False,
        description="Print the synastry relationship score in the info panel. Inert here — a progressed biwheel carries no such score.",
    )
    show_ayanamsa_value: bool = Field(
        default=False,
        description="Append the ayanamsa offset in degrees to the zodiac line of the info panel. Sidereal charts only.",
    )
    show_polar_fallback_note: bool = Field(
        default=False,
        description="Mark the house-system line when a polar latitude forced the engine to substitute the requested system.",
    )

    @model_validator(mode="after")
    def validate_target(self) -> "SecondaryProgressionsRequestModel":
        if (self.target_iso_utc_datetime is None) == (self.target_year is None):
            raise ValueError("Provide exactly one of 'target_iso_utc_datetime' or 'target_year'.")
        return self

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Canonicalize aliased point names (e.g. 'asc', 'mc', 'north_node') so
        they are not silently dropped by the factory point matcher."""
        return _normalize_active_points(value)


class SolarArcDirectionsRequestModel(StrictRequestModel):
    """Request payload for computing solar arc directions."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject to direct.")
    target_iso_utc_datetime: Optional[str] = Field(
        default=None,
        description="ISO-8601 UTC target timestamp. Mutually exclusive with target_year.",
    )
    target_year: Optional[int] = Field(
        default=None,
        description="Convenience target year (Jan 1 at 00:00 UTC). Mutually exclusive with target_iso_utc_datetime.",
        ge=-13200,
        le=9999,
    )
    active_points: Optional[list[str]] = Field(
        default=None,
        description="Natal points to direct. Defaults to the standard 14-point set.",
    )
    compute_aspects: bool = Field(
        default=True,
        description="If false, skip directed-to-natal aspect detection.",
    )
    aspect_orb: float = Field(
        default=3.0,
        description="Orb in degrees for directed-to-natal aspect detection (Astro-Seek default: 3°).",
        ge=0.1,
        le=10.0,
    )
    aspects: Optional[list[str]] = Field(
        default=None,
        description="Aspect names to detect. Defaults to all configured aspects.",
    )
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustmentValue]] = Field(
        default=None,
        description="Per-point orb adjustment table (point name → degrees added to the aspect base orb). When omitted, no adjustment applies — solar arc uses a flat, tight orb. An entry can also be an object of aspect name → degrees with '*' as the default for aspects not listed.",
        examples=[{"Sun": 1.5, "Moon": 1.5}, {"Sun": {"*": 1.5, "conjunction": 3.0}}],
    )

    @field_validator("point_orb_adjustments")
    @classmethod
    def _check_point_orb_capability(cls, value):
        return _check_point_orb_adjustments_capability(value)

    point_orb_adjustment_strategy: OrbAdjustmentStrategy = Field(
        default="max_explicit",
        description="How to combine the two points' orb adjustments when a table is supplied.",
    )
    axis_orb_limit: Optional[float] = Field(
        default=None,
        description="Override the maximum orb (in degrees) for aspects involving axial points (ASC, MC, DSC, IC).",
        ge=0,
        le=30,
    )
    distribution_method: DistributionMethod = Field(
        default="weighted",
        description="Element/quality distribution strategy for the directed chart.",
    )
    custom_distribution_weights: Optional[Mapping[str, float]] = Field(
        default=None,
        description="Custom weights used when distribution_method='weighted'.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include the directed-to-natal house overlay comparison.",
    )
    theme: Optional[KerykeionChartTheme] = Field(
        default="classic",
        description="Visual theme for the generated SVG chart.",
    )
    style: KerykeionChartStyle = Field(
        default="classic",
        description="Chart rendering style: 'classic' (traditional wheel) or 'modern' (concentric rings).",
        examples=list(get_args(KerykeionChartStyle)),
    )
    glyph_size: KerykeionGlyphSize = Field(
        default="medium",
        description=(
            "Size of the planet cluster on the wheel: 'small', 'medium' (default) or 'large' "
            "(the planet glyph at the classic style's own size, "
            "in the default configuration — zodiac background ring active). "
            "Only affects 'modern' style \u2014 the classic wheel draws a fixed-size glyph."
        ),
        examples=list(get_args(KerykeionGlyphSize)),
    )
    show_zodiac_background_ring: bool = Field(
        default=True,
        description="Draw the outer colored zodiac ring. Only affects 'modern' style.",
    )
    transparent_background: bool = Field(
        default=False,
        description="Render chart with transparent background instead of theme default.",
    )
    show_motion_state: bool = Field(
        default=False,
        description="Label stationary planets on the wheel: 'SR' when turning retrograde, 'SD' when turning direct.",
    )
    show_out_of_bounds: bool = Field(
        default=False,
        description="Badge points whose declination is beyond the Sun's extremes (about ±23°26') with 'OOB'.",
    )
    show_aspect_movement: bool = Field(
        default=False,
        description="Dash the aspect lines of separating aspects; applying aspects stay solid.",
    )
    show_relationship_score: bool = Field(
        default=False,
        description="Print the synastry relationship score in the info panel. Inert here — a progressed biwheel carries no such score.",
    )
    show_ayanamsa_value: bool = Field(
        default=False,
        description="Append the ayanamsa offset in degrees to the zodiac line of the info panel. Sidereal charts only.",
    )
    show_polar_fallback_note: bool = Field(
        default=False,
        description="Mark the house-system line when a polar latitude forced the engine to substitute the requested system.",
    )

    @model_validator(mode="after")
    def validate_target(self) -> "SolarArcDirectionsRequestModel":
        if (self.target_iso_utc_datetime is None) == (self.target_year is None):
            raise ValueError("Provide exactly one of 'target_iso_utc_datetime' or 'target_year'.")
        return self

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Canonicalize aliased point names (e.g. 'asc', 'mc', 'north_node') so
        they are not silently dropped by the factory point matcher."""
        return _normalize_active_points(value)
