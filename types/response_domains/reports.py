"""Reports response models."""

from pydantic import Field


from ..response_core import StatusResponseModel


class ReportResponseModel(StatusResponseModel):
    """Response payload for text report generation."""

    report: str = Field(description="Generated text report for the astrological subject.")
