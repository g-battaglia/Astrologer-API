"""Moon request models."""

from __future__ import annotations
from typing import Optional, get_args
from pydantic import Field, field_validator, model_validator
from kerykeion.schemas import (
    SiderealMode,
    ZodiacType,
)
from ..request_core import StrictRequestModel, _check_timezone, _validate_scan_range


class MoonVocWindowsRequestModel(StrictRequestModel):
    """Request payload for void-of-course Moon windows over a date range."""

    model_config = {"extra": "forbid"}

    start_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-01'.",
    )
    end_date: str = Field(
        description="ISO date or datetime (treated as UTC), e.g. '2026-01-31'.",
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Optional IANA timezone: when set, each window also carries *_local ISO strings.",
        examples=["Europe/Rome"],
    )
    zodiac_type: ZodiacType = Field(
        default="Tropical",
        description="Zodiac type used for the calculation (sign boundaries shift under a sidereal zodiac).",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_range(self) -> "MoonVocWindowsRequestModel":
        _validate_scan_range(self.start_date, self.end_date, 366, "~1 year")
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")
        return self
