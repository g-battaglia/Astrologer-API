"""Locational request models."""

from __future__ import annotations
from typing import Optional, Union
from pydantic import Field, field_validator, model_validator
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_POINTS,
)
from ..request_core import ActivePointName, StrictRequestModel, SubjectModel, _check_timezone, _normalize_active_points


class RelocatedChartRequestModel(StrictRequestModel):
    """Request payload for relocating a natal chart to a new location."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Original natal subject to relocate.")
    active_points: Optional[list[Union[ActivePointName, str]]] = Field(
        default=None,
        description="Override the active points used for the relocated chart (e.g. include 'Vertex' or Arabic Parts, which relocation recomputes).",
        examples=[DEFAULT_ACTIVE_POINTS],
    )
    new_latitude: float = Field(
        description="Latitude of the new location.",
        ge=-90,
        le=90,
    )
    new_longitude: float = Field(
        description="Longitude of the new location.",
        ge=-180,
        le=180,
    )
    new_city: str = Field(
        default="Relocated",
        description="City name for the new location.",
    )
    new_nation: str = Field(
        default="",
        description="Nation code for the new location.",
    )
    new_timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone for the new location. If omitted, original timezone is kept.",
    )

    @field_validator("new_timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value:
            _check_timezone(value)
        return value

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)


class AstroCartographyRequestModel(StrictRequestModel):
    """Request payload for computing astro-cartography (ACG) planetary lines."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject for ACG line calculation.")
    step: float = Field(
        default=1.0,
        description="Longitude step in degrees for line resolution.",
        ge=0.1,
        le=10.0,
    )
    tolerance: Optional[float] = Field(
        default=None,
        description="Altitude tolerance in degrees for line detection.",
    )
    lat_range_min: float = Field(
        default=-66,
        description="Minimum latitude for the search range.",
        ge=-90,
        le=90,
    )
    lat_range_max: float = Field(
        default=66,
        description="Maximum latitude for the search range.",
        ge=-90,
        le=90,
    )
    planets: Optional[list[str]] = Field(
        default=None,
        description="Planets to calculate ACG lines for. Defaults to all if omitted.",
    )

    @field_validator("planets", mode="before")
    @classmethod
    def normalize_planets(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)

    @model_validator(mode="after")
    def validate_lat_range(self) -> "AstroCartographyRequestModel":
        if self.lat_range_min >= self.lat_range_max:
            raise ValueError("lat_range_min must be less than lat_range_max.")
        return self
