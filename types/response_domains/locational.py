"""Locational response models."""

from pydantic import Field

from kerykeion import (
    ACGLineModel,
)
from kerykeion.schemas import (
    AstrologicalSubjectModel,
)


from ..response_core import StatusResponseModel


class RelocatedChartResponseModel(StatusResponseModel):
    """Response payload for relocated chart calculation."""

    subject: AstrologicalSubjectModel = Field(
        description="Relocated astrological subject (original planets, recalculated houses/angles).",
    )


class AstroCartographyResponseModel(StatusResponseModel):
    """Response payload for astro-cartography (ACG) line calculation."""

    lines: list[ACGLineModel] = Field(
        default_factory=list,
        description="List of ACG lines with planet, line_type (ASC/DSC/MC/IC), and coordinate points.",
    )
