"""Transits request models."""

from __future__ import annotations
from typing import Literal
from pydantic import Field, model_validator
from ..request_core import ChartDataConfigurationMixin, SubjectModel


class TransitEventsRequestModel(ChartDataConfigurationMixin):
    """Request payload for computing transit events over a time range with optional exact moment refinement."""

    subject: SubjectModel = Field(description="Natal subject to track transits against.")
    start_date: str = Field(
        description="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
        examples=["2025-01-01"],
    )
    end_date: str = Field(
        description="End date in ISO format.",
        examples=["2025-12-31"],
    )
    step_type: Literal["days", "hours", "minutes"] = Field(
        default="days",
        description=("Ephemeris sampling interval. Use 'hours' for fast movers (the Moon traverses ~13°/day, so daily steps undersample it)."),
    )
    step_days: int = Field(
        default=1,
        description="Step size in `step_type` units (e.g. 1 day, or 6 with step_type='hours').",
        ge=1,
        le=30,
    )
    refine_exact_moments: bool = Field(
        default=False,
        description="Iteratively refine each exact transit moment between adjacent samples (ternary search). Precision depends on `refinement_iterations`.",
    )
    refinement_iterations: int = Field(
        default=12,
        description="Refinement iterations (higher = more precise). Each step keeps 2/3 of the bracket: at daily sampling the default 12 lands within a few minutes, and 30 reaches sub-second.",
        ge=1,
        le=30,
    )
    include_transit_subjects: bool = Field(
        default=False,
        description=(
            "transit-daily-aspects only: attach the full transiting chart to every snapshot as "
            "`transits[].subject` (positions, signs, motion state, lunar phase, and essential dignities "
            "when `subject.calculate_dignities` is set), for consumers that need per-sample positions "
            "next to the aspects. Adds roughly one chart per sample to the payload, so narrow "
            "`active_points` and the range accordingly. Ignored by transit-aspect-timeline."
        ),
    )

    @model_validator(mode="after")
    def validate_range(self) -> "TransitEventsRequestModel":
        # Local import avoids a module cycle: transit_series imports the sample
        # counter and constants defined by this request module.
        from ...utils.transit_series import validate_transit_range

        validate_transit_range(
            self.start_date,
            self.end_date,
            timezone_name=self.subject.timezone or "Etc/UTC",
            is_dst=self.subject.is_dst,
            step_type=self.step_type,
            step=self.step_days,
        )
        return self

    @model_validator(mode="after")
    def reject_inapplicable_chart_options(self) -> "TransitEventsRequestModel":
        unsupported: list[str] = []
        if self.point_orb_adjustments is not None:
            unsupported.append("point_orb_adjustments")
        if self.point_orb_adjustment_strategy != "max_explicit":
            unsupported.append("point_orb_adjustment_strategy")
        if self.distribution_method != "weighted":
            unsupported.append("distribution_method")
        if self.custom_distribution_weights is not None:
            unsupported.append("custom_distribution_weights")
        if unsupported:
            raise ValueError("Transit time-range endpoints do not support chart-distribution or point-orb options: " + ", ".join(unsupported) + ". Remove them instead of relying on an ignored value.")
        return self
