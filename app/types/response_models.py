from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    DualChartDataModel,
    MoonPhaseOverviewModel,
    RelationshipScoreAspectModel,
    SingleChartDataModel,
    ScoreBreakdownItemModel,
)


class StatusResponseModel(BaseModel):
    """Response payload containing only the status field."""

    status: str = Field(description="The status of the response.")


class ApiStatusResponseModel(StatusResponseModel):
    """Response payload for the API root status endpoint."""

    environment: str = Field(description="Deployment environment identifier.")
    debug: bool = Field(description="Whether debug mode is enabled.")


class SubjectResponseModel(StatusResponseModel):
    """Response payload containing a single astrological subject."""

    subject: AstrologicalSubjectModel = Field(
        description="Computed astrological subject."
    )


class ChartDataResponseModel(StatusResponseModel):
    """Response payload returning serialized chart data."""

    chart_data: Union[SingleChartDataModel, DualChartDataModel] = Field(
        description="Serialized chart data payload."
    )


class ChartResponseModel(ChartDataResponseModel):
    """Response payload returning chart data with optional rendered SVG assets."""

    chart: Optional[str] = Field(
        default=None,
        description="SVG representation of the chart when split charts are disabled.",
    )
    chart_wheel: Optional[str] = Field(
        default=None,
        description="SVG representation of the chart wheel when split charts are enabled.",
    )
    chart_grid: Optional[str] = Field(
        default=None,
        description="SVG representation of the aspect grid when split charts are enabled.",
    )


class ReturnChartResponseModel(ChartResponseModel):
    """Response payload for solar and lunar return chart requests."""

    return_type: Literal["Solar", "Lunar"] = Field(
        description="Type of planetary return."
    )
    wheel_type: Literal["dual", "single"] = Field(
        description="Rendered wheel configuration."
    )


class CompatibilityScoreResponseModel(StatusResponseModel):
    """Response payload for the compatibility score endpoint."""

    score: Optional[float] = Field(
        default=None,
        description="Numeric relationship score.",
    )
    score_description: Optional[str] = Field(
        default=None,
        description="Textual description of the score.",
    )
    is_destiny_sign: Optional[bool] = Field(
        default=None,
        description="Whether the subjects form a destiny-sign relationship.",
    )
    aspects: list[RelationshipScoreAspectModel] = Field(
        default_factory=list,
        description="Aspects considered for the score calculation.",
    )
    score_breakdown: list[ScoreBreakdownItemModel] = Field(
        default_factory=list,
        description="Breakdown of the scoring rules and points contributing to the total score.",
    )
    chart_data: DualChartDataModel = Field(
        description="Underlying chart data used to compute the score."
    )


class SubjectContextResponseModel(StatusResponseModel):
    """Response payload containing a single astrological subject with AI context."""

    subject_context: str = Field(
        description="AI-optimized context string for the subject."
    )
    subject: AstrologicalSubjectModel = Field(
        description="Computed astrological subject."
    )


class ContextResponseModel(StatusResponseModel):
    """Response payload returning chart data with AI-optimized context."""

    context: str = Field(description="AI-optimized context string for the chart data.")
    chart_data: Union[SingleChartDataModel, DualChartDataModel] = Field(
        description="Serialized chart data payload."
    )


class MoonPhaseResponseModel(StatusResponseModel):
    """Response payload for moon phase details."""

    moon_phase_overview: MoonPhaseOverviewModel = Field(
        description="Detailed moon phase overview including illumination, upcoming phases, eclipses, and sun info."
    )


class MoonPhaseContextResponseModel(StatusResponseModel):
    """Response payload for moon phase details with AI-optimized context."""

    context: str = Field(
        description="AI-optimized XML context string for the moon phase overview."
    )
    moon_phase_overview: MoonPhaseOverviewModel = Field(
        description="Detailed moon phase overview including illumination, upcoming phases, eclipses, and sun info."
    )


class ReturnContextResponseModel(ContextResponseModel):
    """Response payload for solar and lunar return context requests."""

    return_type: Literal["Solar", "Lunar"] = Field(
        description="Type of planetary return."
    )
    wheel_type: Literal["dual", "single"] = Field(
        description="Rendered wheel configuration."
    )
