"""Analysis response models."""

from typing import Optional

from pydantic import Field

from kerykeion import (
    MidpointModel,
    PlanetaryNodeModel,
)
from kerykeion.schemas import (
    AspectModel,
    DominantsModel,
)


from ..response_core import StatusResponseModel


class PlanetaryNodesResponseModel(StatusResponseModel):
    """Response payload for planetary nodes and apsides calculation."""

    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime of the calculation moment.")
    julian_day: Optional[float] = Field(default=None, description="Julian Day of the calculation moment.")
    method: str = Field(description="Calculation method used ('mean' or 'osculating').")
    nodes: list[PlanetaryNodeModel] = Field(
        default_factory=list,
        description="List of planetary node data (ascending/descending nodes, perihelion/aphelion).",
    )


class MidpointsResponseModel(StatusResponseModel):
    """Response payload for midpoint table calculation."""

    midpoints: list[MidpointModel] = Field(
        default_factory=list,
        description=(
            "List of midpoint entries. Each carries point_a / point_b, the midpoint "
            "longitude on the shorter arc, sign + position-within-sign, the 90 deg "
            "dial position, and any third points that aspect the midpoint within orb."
        ),
    )


class MidpointsContextResponseModel(StatusResponseModel):
    """Response payload for the midpoints context endpoint."""

    context: str = Field(description="AI-optimized context string for the midpoint table.")
    midpoints: list[MidpointModel] = Field(
        default_factory=list,
        description="List of midpoint entries (see `MidpointModel`).",
    )


class DominantsResponseModel(StatusResponseModel):
    """Response payload for the dominants endpoint."""

    dominants: DominantsModel = Field(
        description="Computed dominants: ranked planets, signs, elements, modalities and houses "
        "(plus polarity, hemispheres and quadrants for the modern method), the convenience "
        "'dominant_*' winners, and the optional per-rule 'score_breakdown'."
    )


class DeclinationAspectsResponseModel(StatusResponseModel):
    """Response payload for declination aspects calculation."""

    aspects: list[AspectModel] = Field(
        default_factory=list,
        description="List of declination aspects (parallel / contra-parallel).",
    )
