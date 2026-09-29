"""Traditional request models."""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import Field
from ..request_core import StrictRequestModel, SubjectModel


class ZodiacalReleasingRequestModel(StrictRequestModel):
    """Request payload for computing zodiacal releasing (aphesis) from a lot."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject (requires a known birth time).")
    lot: Literal["fortune", "spirit"] = Field(
        default="fortune",
        description="Lot to release from: 'fortune' (body/circumstances) or 'spirit' (mind/action).",
    )
    levels: int = Field(
        default=2,
        description="Subdivision levels to compute (1-4). L1/L2 are full; deeper levels follow the target-date path.",
        ge=1,
        le=4,
    )
    target_date: Optional[str] = Field(
        default=None,
        description="ISO date (YYYY-MM-DD) used to mark the current period chain.",
    )
    life_cap_years: int = Field(
        default=100,
        description="Upper bound (in years) on how far the releasing sequence is unrolled.",
        ge=1,
        le=120,
    )


class ProfectionsRequestModel(StrictRequestModel):
    """Request payload for computing annual profections."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Natal subject (requires the twelve house cusps).")
    target_date: Optional[str] = Field(
        default=None,
        description=("ISO date (YYYY-MM-DD) the 'current' profection year is resolved against. Defaults to today in the subject's own timezone."),
    )
    years_before: int = Field(
        default=3,
        description="Past profection years to include in the table.",
        ge=0,
        le=120,
    )
    years_after: int = Field(
        default=4,
        description="Future profection years to include in the table.",
        ge=0,
        le=120,
    )


class FirdariaRequestModel(StrictRequestModel):
    """Request payload for computing the firdaria time-lord periods."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description=("Natal subject. Requires a real sect (is_diurnal): a midpoint composite has no horizon and is rejected."))
    target_date: Optional[str] = Field(
        default=None,
        description=("ISO date (YYYY-MM-DD) the current period/sub-period are resolved against. Defaults to now in the subject's own timezone."),
    )
    life_cap_years: int = Field(
        default=120,
        description="How far the firdaria timeline is unrolled, in years of life.",
        ge=1,
        le=120,
    )


class HoraryIndicatorsRequestModel(StrictRequestModel):
    """Request payload for horary significators and considerations."""

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Chart cast for the moment of the question.")
    is_moon_void: Optional[bool] = Field(
        default=None,
        description=("Whether the Moon is void of course, when known (from the void-of-course search). Omitted: the two Moon considerations are simply not evaluated."),
    )
