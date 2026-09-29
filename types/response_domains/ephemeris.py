"""Ephemeris response models."""

from typing import Optional

from pydantic import BaseModel, Field

from kerykeion.schemas import (
    EphemerisDictModel,
)


from ..response_core import StatusResponseModel


class FixedStarsTruncationModel(BaseModel):
    """Declared truncation of the requested fixed-star list.

    When the requested stars would push the ephemeris past its work budget,
    the route serves the affordable prefix of the request (a deterministic
    cut, in the caller's own order) and says so here — clients never need to
    mirror the engine's cost model to pre-trim.
    """

    requested: int = Field(description="How many fixed stars the request carried.")
    served: int = Field(description="How many fit the work budget and were calculated.")
    dropped: list[str] = Field(
        default_factory=list,
        description="The star names that were dropped, in request order.",
    )


class EphemerisResponseModel(StatusResponseModel):
    """Response payload for ephemeris data generation."""

    ephemeris: list[EphemerisDictModel] = Field(
        default_factory=list,
        description="Ephemeris data points with planetary positions and house cusps.",
    )
    fixed_stars_truncated: Optional[FixedStarsTruncationModel] = Field(
        default=None,
        description=("Present only when the requested active_fixed_stars exceeded the work budget: how many were requested/served and which were dropped."),
    )
