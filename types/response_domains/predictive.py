"""Predictive response models."""

from typing import Optional

from pydantic import Field

from kerykeion import (
    PrimaryDirectionModel,
    ProgressedToNatalAspectModel,
    SolarArcSubjectModel,
    SpeculumEntryModel,
)
from kerykeion.schemas import ProgressedPointModel
from kerykeion.schemas import (
    AstrologicalSubjectModel,
    DualChartDataModel,
)


from ..response_core import StatusResponseModel


class PrimaryDirectionsResponseModel(StatusResponseModel):
    """Response payload for primary directions calculation."""

    directions: list[PrimaryDirectionModel] = Field(
        default_factory=list,
        description="List of primary directions with promissor, significator, aspect, arc, and years.",
    )
    speculum: list[SpeculumEntryModel] = Field(
        default_factory=list,
        description="Speculum table with RA, declination, semi-arc, and pole for each point.",
    )


class SecondaryProgressionsResponseModel(StatusResponseModel):
    """Response payload for secondary progressions calculation."""

    progressed_subject: AstrologicalSubjectModel = Field(
        description=("Progressed AstrologicalSubjectModel — same shape as a regular natal subject, with year/month/day fields referring to the progressed moment."),
    )
    target_iso_utc_datetime: Optional[str] = Field(default=None, description="Resolved ISO-8601 UTC timestamp of the target moment.")
    ephemeris_iso_utc_datetime: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp of the progressed ephemeris moment.")
    progressed_points: list[ProgressedPointModel] = Field(
        default_factory=list,
        description=("Natal-vs-progressed comparison per point, carrying the engine's sign_changed ingress flag (the progressions counterpart of the solar-arc flag)."),
    )
    progressed_to_natal_aspects: list[ProgressedToNatalAspectModel] = Field(
        default_factory=list,
        description="Aspects between progressed and natal points.",
    )


class SecondaryProgressionsContextResponseModel(StatusResponseModel):
    """Response payload for the secondary progressions context endpoint."""

    context: str = Field(description="AI-optimized context string for the progressed chart.")
    progressed_subject: AstrologicalSubjectModel = Field(
        description="Progressed AstrologicalSubjectModel for the target moment.",
    )


class SolarArcContextResponseModel(StatusResponseModel):
    """Response payload for the solar arc directions context endpoint."""

    context: str = Field(description="AI-optimized context string for the directed chart.")
    solar_arc_subject: SolarArcSubjectModel = Field(
        description="SolarArcSubjectModel: arc, directed points, directed-to-natal aspects.",
    )


class PrimaryDirectionsContextResponseModel(StatusResponseModel):
    """Response payload for the primary directions context endpoint."""

    context: str = Field(description="XML context string listing the primary directions.")
    directions: list[PrimaryDirectionModel] = Field(
        default_factory=list,
        description="Primary directions with promissor, significator, aspect, arc, and years.",
    )
    speculum: list[SpeculumEntryModel] = Field(
        default_factory=list,
        description="Speculum table with RA, declination, semi-arc, and pole for each point.",
    )


class ProgressionChartResponseModel(StatusResponseModel):
    """Response payload for the progression / solar-arc biwheel chart endpoints."""

    chart_wheel: str = Field(description="SVG of the biwheel (no aspect grid).")
    chart_grid: str = Field(description="SVG of the aspect grid (separate panel).")
    chart_data: DualChartDataModel = Field(description="Progression-type chart data.")


class SolarArcDirectionsResponseModel(StatusResponseModel):
    """Response payload for solar arc directions calculation."""

    solar_arc_subject: SolarArcSubjectModel = Field(
        description=(
            "SolarArcSubjectModel — solar_arc (signed degrees), directed_points (natal vs directed positions, sign_changed flag), and directed_to_natal_aspects (the actionable timing list)."
        ),
    )
