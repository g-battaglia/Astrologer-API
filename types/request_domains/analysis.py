"""Analysis request models."""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import Field, field_validator
from ..request_core import StrictRequestModel, SubjectModel, _normalize_active_points


class PlanetaryNodesRequestModel(StrictRequestModel):
    """Request payload for computing planetary nodes and apsides."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject defining the moment for node calculation.")
    method: Literal["mean", "osculating"] = Field(
        default="mean",
        description="Node calculation method: 'mean' (averaged) or 'osculating' (instantaneous).",
    )
    planets: Optional[list[str]] = Field(
        default=None,
        description="Planets to compute nodes for. Defaults to all if omitted.",
    )


class MidpointsRequestModel(StrictRequestModel):
    """Request payload for computing the midpoint table of a chart."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal/event subject to compute midpoints for.")
    active_points: Optional[list[str]] = Field(
        default=None,
        description="Points to use as midpoint constituents. Defaults to the standard 14-point set.",
    )
    aspect_orb: float = Field(
        default=1.0,
        description="Orb in degrees for aspect-to-midpoint detection.",
        ge=0.1,
        le=10.0,
    )
    aspects: Optional[list[str]] = Field(
        default=None,
        description="Aspect names to detect on midpoints. Defaults to all configured aspects.",
    )
    compute_aspects: bool = Field(
        default=True,
        description="If false, skip aspect-to-midpoint detection and return only the midpoint table.",
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Canonicalize aliased point names (e.g. 'asc', 'mc', 'north_node') so
        they are not silently dropped by the midpoint constituent matcher."""
        return _normalize_active_points(value)


class DeclinationAspectsRequestModel(StrictRequestModel):
    """Request payload for computing declination aspects (parallel/contra-parallel) within a single chart."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject for declination aspect calculation.")
    active_points: Optional[list[str]] = Field(
        default=None,
        description="Points to include. Defaults to DEFAULT_ACTIVE_POINTS if omitted.",
    )
    orb: float = Field(
        default=1.0,
        description="Maximum orb in degrees for declination aspects.",
        ge=0.1,
        le=5.0,
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)


class DualDeclinationAspectsRequestModel(StrictRequestModel):
    """Request payload for computing declination aspects between two charts."""

    model_config = {"extra": "forbid"}

    first_subject: SubjectModel = Field(description="First subject.")
    second_subject: SubjectModel = Field(description="Second subject.")
    active_points: Optional[list[str]] = Field(
        default=None,
        description="Points to include. Defaults to DEFAULT_ACTIVE_POINTS if omitted.",
    )
    orb: float = Field(
        default=1.0,
        description="Maximum orb in degrees for declination aspects.",
        ge=0.1,
        le=5.0,
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)
