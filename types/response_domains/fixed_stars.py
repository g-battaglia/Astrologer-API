"""Fixed Stars response models."""

from pydantic import Field

from kerykeion.schemas import (
    KerykeionPointModel,
)


from ..response_core import StatusResponseModel


class FixedStarDiscoveryResponseModel(StatusResponseModel):
    """Response payload for fixed star discovery."""

    stars: list[KerykeionPointModel] = Field(
        default_factory=list,
        description="List of prominent fixed stars found in conjunction with chart points.",
    )
