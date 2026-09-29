"""Ephemeris request models."""

from __future__ import annotations
from typing import Literal, Optional, Union
from pydantic import Field, field_validator, model_validator
from kerykeion.schemas import (
    HousesSystemIdentifier,
    PerspectiveType,
    SiderealMode,
    ZodiacType,
)
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_POINTS,
)
from ..request_core import (
    ActivePointName,
    EPHEMERIS_MAX_POINT_CALCULATIONS,
    EPHEMERIS_MAX_SAMPLES,
    FIXED_STAR_WORK_UNIT_WEIGHT,
    StrictRequestModel,
    _check_timezone,
    _count_ephemeris_samples,
    _normalize_active_fixed_stars,
    _normalize_active_points,
)


class EphemerisRequestModel(StrictRequestModel):
    """Request payload for generating ephemeris tables over a date range."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
        examples=["2025-01-01"],
    )
    end_date: str = Field(
        description="End date in ISO format.",
        examples=["2025-01-31"],
    )
    step_type: Literal["days", "hours", "minutes"] = Field(
        default="days",
        description="Interval type for ephemeris snapshots.",
    )
    step: int = Field(
        default=1,
        description="Step size (e.g. 1 day, 6 hours).",
        ge=1,
    )
    latitude: float = Field(
        default=51.4769,
        description="Observer latitude.",
        ge=-90,
        le=90,
    )
    longitude: float = Field(
        default=0.0005,
        description="Observer longitude.",
        ge=-180,
        le=180,
    )
    timezone: str = Field(
        default="Etc/UTC",
        description="IANA timezone identifier.",
    )
    zodiac_type: Optional[ZodiacType] = Field(default="Tropical", description="Zodiac system.")
    sidereal_mode: Optional[SiderealMode] = Field(default=None, description="Sidereal mode.")
    houses_system_identifier: Optional[HousesSystemIdentifier] = Field(default="P", description="House system.")
    perspective_type: Optional[PerspectiveType] = Field(default="Apparent Geocentric", description="Perspective.")
    is_dst: Optional[bool] = Field(
        default=None,
        description="Daylight-saving disambiguation for ambiguous local times. None lets the library decide.",
    )
    custom_ayanamsa_t0: Optional[float] = Field(
        default=None,
        description="Reference epoch as Julian Day for the USER sidereal mode. Required when sidereal_mode='USER'.",
        examples=[2451545.0],
    )
    custom_ayanamsa_ayan_t0: Optional[float] = Field(
        default=None,
        description="Ayanamsa offset in degrees at the reference epoch. Required when sidereal_mode='USER'.",
        examples=[23.5],
    )
    active_points: Optional[list[Union[ActivePointName, str]]] = Field(
        default=None,
        min_length=1,
        description=("Points calculated at every sample. Fixed stars are not active points and must not be included here."),
        examples=[DEFAULT_ACTIVE_POINTS],
    )
    active_fixed_stars: Optional[list[str]] = Field(
        default=None,
        description=(
            "Fixed star names computed at every sample from the libephemeris catalog "
            "(no automatic defaults; use `GET /api/v6/fixed-stars/catalog` to discover names). "
            "Fixed stars are not active points and must not be included in `active_points`. "
            "An empty list is equivalent to omitting the field. When requested, every "
            "sample carries a `fixed_stars` key with the calculated star point models."
        ),
        examples=[["Sirius", "Vega"]],
    )
    include_houses: bool = Field(
        default=True,
        description="Include the twelve house-cusp objects in every sample.",
    )
    omit_nulls: bool = Field(
        default=False,
        description="Omit unset optional point fields to reduce batch response size.",
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)

    @field_validator("active_fixed_stars", mode="before")
    @classmethod
    def normalize_active_fixed_stars(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_fixed_stars(value)

    @field_validator("timezone")
    @classmethod
    def validate_tz(cls, value: str) -> str:
        _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_range(self) -> "EphemerisRequestModel":
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.sidereal_mode == "USER" and (self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None):
            raise ValueError("custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are required when sidereal_mode='USER'.")

        points = _count_ephemeris_samples(
            self.start_date,
            self.end_date,
            timezone_name=self.timezone,
            is_dst=self.is_dst,
            step_type=self.step_type,
            step=self.step,
        )
        if points > EPHEMERIS_MAX_SAMPLES:
            raise ValueError(f"Range too large: {points} ephemeris samples requested (max {EPHEMERIS_MAX_SAMPLES}). Reduce the date span or increase the step.")

        selected_points = self.active_points or list(DEFAULT_ACTIVE_POINTS)
        selected_stars = self.active_fixed_stars or []
        # The budget rejects a request only when the POINTS alone exceed it:
        # that is a genuinely oversized request no trimming can save. A star
        # overflow is instead handled by the route, which truncates the star
        # list deterministically and DECLARES the truncation in the response —
        # so clients never need to mirror this cost model to pre-trim.
        points_only_work = points * len(selected_points)
        if points_only_work > EPHEMERIS_MAX_POINT_CALCULATIONS:
            work_units = points * (len(selected_points) + FIXED_STAR_WORK_UNIT_WEIGHT * len(selected_stars))
            raise ValueError(
                f"Ephemeris request costs {work_units} point-sample equivalents (fixed stars weigh {FIXED_STAR_WORK_UNIT_WEIGHT}x a point; max {EPHEMERIS_MAX_POINT_CALCULATIONS}). Reduce the date span, increase the step, or request fewer active_points."
            )
        return self
