"""Fixed Stars request models."""

from __future__ import annotations
from pydantic import Field
from ..request_core import StrictRequestModel, SubjectModel


class FixedStarDiscoveryRequestModel(StrictRequestModel):
    """Request payload for discovering prominent fixed stars in a chart."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject to search for prominent fixed stars.")
    orb: float = Field(
        default=1.0,
        description="Maximum orb in degrees for conjunction with chart points.",
        ge=0.1,
        le=10.0,
    )
