"""Transits response models."""

from typing import Optional

from pydantic import BaseModel, Field

from kerykeion.schemas import (
    AstrologicalSubjectModel,
    DualChartDataModel,
    TransitEventModel,
    TransitMomentModel,
)


from ..response_core import StatusResponseModel


class TransitBatchEntryModel(BaseModel):
    """One per-date entry of a transit batch response."""

    date: str = Field(description="ISO date(time) of the transit moment.")
    chart_data: DualChartDataModel = Field(description="Transit chart data for the date.")


class TransitBatchResponseModel(StatusResponseModel):
    """Response payload for the batch transit endpoint."""

    results: list[TransitBatchEntryModel] = Field(
        default_factory=list,
        description="Per-date transit chart data, in chronological order.",
    )


class TransitEventsResponseModel(StatusResponseModel):
    """Response payload for transit events calculation."""

    events: list[TransitEventModel] = Field(
        default_factory=list,
        description="Transit events with applying start, exact moment, and separating end.",
    )
    subject: Optional[AstrologicalSubjectModel] = Field(
        default=None,
        description="Natal subject data.",
    )


class TransitMomentsResponseModel(StatusResponseModel):
    """Response payload for transit moment snapshots."""

    transits: list[TransitMomentModel] = Field(
        default_factory=list,
        description=(
            "Transit moment snapshots with active aspects at each date. Each snapshot carries "
            "`subject` — the full transiting chart it was computed from — only when the request "
            "set `include_transit_subjects`."
        ),
    )
    subject: Optional[AstrologicalSubjectModel] = Field(default=None, description="Natal subject data.")
    dates: Optional[list[str]] = Field(default=None, description="ISO dates of transit moments.")
