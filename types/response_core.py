from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from kerykeion.schemas import (
    AstrologicalSubjectModel,
    DualChartDataModel,
    MoonPhaseLocationModel,
    MoonPhaseOverviewModel,
    RelationshipScoreAspectModel,
    SingleChartDataModel,
    ScoreBreakdownItemModel,
)
from kerykeion.schemas import RelationshipScoreDescription

# ``SolarPhaseThresholdsModel`` arrived with the a91 pin. Kept out of the block
# import above and guarded, because this module is imported by ``app.main``:
# against an engine that predates the symbol the top-level import would abort
# the whole application at startup — every endpoint down, not just the one
# field that cannot be typed. That is the same deploy-ahead reasoning as the
# local imports in the domain routers, applied where an annotation
# forces the name to exist at module scope.
#
# The fallback widens the annotation instead of narrowing the contract: on such
# an engine ``PlanetaryPhenomenaFactory`` produces no thresholds at all, so the
# field is always ``None`` there and the looser type describes exactly what can
# happen. The committed ``openapi.json`` is generated against the pinned engine,
# so the published schema keeps the real model.
try:
    from kerykeion.schemas import SolarPhaseThresholdsModel
except ImportError:  # pragma: no cover - only reachable on a pre-a91 engine
    SolarPhaseThresholdsModel = Any  # type: ignore[assignment, misc]


class ValidationIssueResponseModel(BaseModel):
    """One field-level request validation failure."""

    loc: list[Union[str, int]] = Field(description="JSON path of the invalid field, beginning with 'body'.")
    msg: str = Field(description="Human-readable validation message.")
    type: str = Field(description="Stable Pydantic validation code.")


class ValidationErrorResponseModel(BaseModel):
    """Actual 422 envelope returned by the global validation handler."""

    status: Literal["ERROR"] = "ERROR"
    message: Literal["Validation failed"] = "Validation failed"
    errors: list[ValidationIssueResponseModel]


class ApplicationErrorResponseModel(BaseModel):
    """Typed application error used by capability and resource guards."""

    status: Literal["ERROR"] = "ERROR"
    message: str
    error_type: str


Public422Response = Union[ValidationErrorResponseModel, ApplicationErrorResponseModel]


class StatusResponseModel(BaseModel):
    """Response payload containing only the status field."""

    status: str = Field(description="The status of the response.")


class FixedStarMetadataResponseModel(BaseModel):
    """Metadata for a single fixed star entry in the catalog."""

    name: str = Field(description="IAU canonical name (e.g. 'Vindemiatrix', 'Deneb Algedi').")
    slug: str = Field(description="URL/identifier-safe slug (spaces -> underscores).")
    hip_number: Optional[int] = Field(default=None, description="Hipparcos catalog number.")
    nomenclature: Optional[str] = Field(default=None, description="Bayer/Flamsteed designation.")
    magnitude: Optional[float] = Field(default=None, description="Visual magnitude.")


class FixedStarsCatalogResponseModel(StatusResponseModel):
    """Response payload listing the full fixed-star catalog (libephemeris)."""

    source: Literal["libephemeris"] = Field(description="Catalog data source.")
    count: int = Field(description="Number of stars in the catalog.")
    stars: list[FixedStarMetadataResponseModel] = Field(description="Catalog entries.")


class ApiStatusResponseModel(StatusResponseModel):
    """Response payload for the API root status endpoint."""

    environment: str = Field(description="Deployment environment identifier.")
    debug: bool = Field(description="Whether debug mode is enabled.")


class EphemerisProbeStatusModel(BaseModel):
    """Sanitized ephemeris state exposed by public probes."""

    ready: bool = Field(description="Whether the sealed ephemeris runtime is usable.")
    state: str = Field(description="Current readiness state.")
    reason: Literal["ready", "provisioning", "worker_warmup", "worker_warmup_failed", "runtime_validation_failed"] = Field(description="Stable, public reason code for the readiness state.")
    precision_tier: Optional[str] = Field(default=None, description="Available ephemeris precision tier, when known.")


class ProbeResponseModel(StatusResponseModel):
    """Public liveness/readiness response."""

    status: Literal["OK", "INITIALIZING"] = Field(description="Probe result.")
    kerykeion_version: str = Field(description="Installed kerykeion version.")
    ephemeris_ready: bool = Field(description="Compatibility alias for ephemeris.ready.")
    ephemeris: EphemerisProbeStatusModel


class SubjectResponseModel(StatusResponseModel):
    """Response payload containing a single astrological subject."""

    subject: AstrologicalSubjectModel = Field(description="Computed astrological subject.")


class ChartDataResponseModel(StatusResponseModel):
    """Response payload returning serialized chart data."""

    chart_data: Union[SingleChartDataModel, DualChartDataModel] = Field(description="Serialized chart data payload.")


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

    return_type: Literal["Solar", "Lunar"] = Field(description="Type of planetary return.")
    wheel_type: Literal["dual", "single"] = Field(description="Rendered wheel configuration.")


class CompatibilityScoreResponseModel(StatusResponseModel):
    """Response payload for the compatibility score endpoint."""

    score: Optional[int] = Field(
        default=None,
        description="Numeric relationship (Ciro Discepolo) score.",
    )
    score_description: Optional[RelationshipScoreDescription] = Field(
        default=None,
        description="Categorical description of the score.",
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
    chart_data: DualChartDataModel = Field(description="Underlying chart data used to compute the score.")


class SubjectContextResponseModel(StatusResponseModel):
    """Response payload containing a single astrological subject with AI context."""

    context: str = Field(description="AI-optimized context string for the subject.")
    subject: AstrologicalSubjectModel = Field(description="Computed astrological subject.")


class ContextResponseModel(StatusResponseModel):
    """Response payload returning chart data with AI-optimized context."""

    context: str = Field(description="AI-optimized context string for the chart data.")
    chart_data: Union[SingleChartDataModel, DualChartDataModel] = Field(description="Serialized chart data payload.")


class PublicMoonPhaseLocationModel(MoonPhaseLocationModel):
    """Wire format after location_precision rounding (the engine's fields are strings)."""

    latitude: float | None = None
    longitude: float | None = None


class PublicMoonPhaseOverviewModel(MoonPhaseOverviewModel):
    """The service serializes moon-phase coordinates as JSON numbers."""

    location: PublicMoonPhaseLocationModel | None = None


class MoonPhaseResponseModel(StatusResponseModel):
    """Response payload for moon phase details."""

    moon_phase_overview: PublicMoonPhaseOverviewModel = Field(description="Detailed moon phase overview including illumination, upcoming phases, eclipses, and sun info.")


class MoonPhaseContextResponseModel(StatusResponseModel):
    """Response payload for moon phase details with AI-optimized context."""

    context: str = Field(description="AI-optimized XML context string for the moon phase overview.")
    moon_phase_overview: PublicMoonPhaseOverviewModel = Field(description="Detailed moon phase overview including illumination, upcoming phases, eclipses, and sun info.")


class ReturnContextResponseModel(ContextResponseModel):
    """Response payload for solar and lunar return context requests."""

    return_type: Literal["Solar", "Lunar"] = Field(description="Type of planetary return.")
    wheel_type: Literal["dual", "single"] = Field(description="Rendered wheel configuration.")
