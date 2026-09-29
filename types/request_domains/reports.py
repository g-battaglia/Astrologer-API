"""Reports request models."""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import Field, model_validator
from ..request_core import StrictRequestModel, SubjectModel


class ReportRequestModel(StrictRequestModel):
    """Request payload for generating a text report.

    Three report kinds are reachable:
    - **Subject** (default): pass only ``subject`` for a bare natal-subject report.
    - **Single chart**: pass ``chart_type='Natal'`` (or set ``include_aspects``) to
      build natal chart data so the aspect table is included.
    - **Dual chart**: pass ``chart_type`` in {'Synastry','Transit','Composite'} with
      ``second_subject`` for a relational report (aspects + house comparison).
    """

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Primary subject for the report.")
    second_subject: Optional[SubjectModel] = Field(
        default=None,
        description="Second subject, required for Synastry/Transit/Composite reports.",
    )
    chart_type: Optional[Literal["Natal", "Synastry", "Transit", "Composite"]] = Field(
        default=None,
        description=(
            "Report kind. Omit for a bare subject report. 'Natal' builds single-chart data (aspect table). 'Synastry'/'Transit'/'Composite' build dual-chart data and require second_subject."
        ),
    )
    include_aspects: Optional[bool] = Field(
        default=None,
        description="Include the aspect table. Implies a chart-data report when true on a single subject.",
    )
    max_aspects: Optional[int] = Field(
        default=None,
        description="Maximum number of aspects to include in the report.",
        ge=1,
        le=100,
    )

    @model_validator(mode="after")
    def validate_report_kind(self) -> "ReportRequestModel":
        dual = {"Synastry", "Transit", "Composite"}
        if self.chart_type in dual and self.second_subject is None:
            raise ValueError(f"second_subject is required when chart_type='{self.chart_type}'.")
        if self.second_subject is not None and self.chart_type not in dual:
            raise ValueError("second_subject requires chart_type in {'Synastry','Transit','Composite'}.")
        return self
