"""Returns response models."""

from typing import Literal, Optional

from pydantic import Field


from ..response_core import ChartResponseModel, ContextResponseModel


class HeliocentricReturnContextResponseModel(ContextResponseModel):
    """Response payload for heliocentric return context requests."""

    return_type: Literal["Heliocentric"] = Field(description="Type of planetary return.")
    planet: Optional[str] = Field(default=None, description="Planet whose heliocentric return was computed (compute mode).")
    wheel_type: Literal["dual", "single"] = Field(description="Rendered wheel configuration.")


class LunarNodeCrossingContextResponseModel(ContextResponseModel):
    """Response payload for lunar node crossing context requests."""

    return_type: Literal["Lunar_Node_Crossing"] = Field(description="Type of planetary return.")
    wheel_type: Literal["dual", "single"] = Field(description="Rendered wheel configuration.")


class HeliocentricReturnChartResponseModel(ChartResponseModel):
    """Response payload for heliocentric return chart."""

    return_type: str = Field(description="Return type (e.g. 'Heliocentric').")
    planet: str = Field(description="Planet of the heliocentric return.")
    wheel_type: Literal["dual", "single"] = Field(description="Wheel configuration.")


class LunarNodeCrossingChartResponseModel(ChartResponseModel):
    """Response payload for lunar node crossing chart."""

    return_type: str = Field(default="Lunar_Node_Crossing", description="Return type.")
    wheel_type: Literal["dual", "single"] = Field(description="Wheel configuration.")
