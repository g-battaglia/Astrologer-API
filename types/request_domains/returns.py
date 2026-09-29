"""Returns request models."""

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import Field, model_validator
from ..request_core import ChartDataConfigurationMixin, ChartRenderingMixin, LUNAR_DERIVED_POINTS, ReturnLocationModel, SubjectModel, _blank_to_none, _normalize_point_name, _validate_iso_datetime


class HeliocentricReturnRequestModel(ChartRenderingMixin):
    """Request payload for heliocentric return chart (with SVG rendering)."""

    subject: SubjectModel = Field(description="Natal subject used for the return calculation.")
    planet: str = Field(
        description="Planet whose heliocentric return to compute (e.g. 'Mars', 'Jupiter').",
        examples=["Mars"],
    )
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.", examples=["2025-05-01T00:00:00+00:00"])
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. 'next' (default) finds the upcoming return; 'previous' finds the most recent past return. Seeded with the instant of a return this API reported, 'next' yields the following return and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution return instants are reported at. Requires the libephemeris backend."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay for dual wheels.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "HeliocentricReturnRequestModel":
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        # Canonicalize case/aliases ('mars' -> 'Mars') — kerykeion's planet
        # lookup is exact-match and would reject the raw name with a 400.
        self.planet = _normalize_point_name(self.planet)
        if self.planet in LUNAR_DERIVED_POINTS:
            raise ValueError(f"Heliocentric returns are undefined for lunar-derived point '{self.planet}'. Use a planet with its own heliocentric orbit (e.g. 'Mars', 'Jupiter').")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self


class HeliocentricReturnDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for heliocentric return data (no SVG)."""

    subject: SubjectModel = Field(description="Natal subject.")
    planet: str = Field(description="Planet whose heliocentric return to compute.", examples=["Mars"])
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.")
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. 'next' (default) finds the upcoming return; 'previous' finds the most recent past return. Seeded with the instant of a return this API reported, 'next' yields the following return and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution return instants are reported at. Requires the libephemeris backend."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "HeliocentricReturnDataRequestModel":
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        # Canonicalize case/aliases ('mars' -> 'Mars') — kerykeion's planet
        # lookup is exact-match and would reject the raw name with a 400.
        self.planet = _normalize_point_name(self.planet)
        if self.planet in LUNAR_DERIVED_POINTS:
            raise ValueError(f"Heliocentric returns are undefined for lunar-derived point '{self.planet}'. Use a planet with its own heliocentric orbit (e.g. 'Mars', 'Jupiter').")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self


class LunarNodeCrossingRequestModel(ChartRenderingMixin):
    """Request payload for lunar node crossing return chart (with SVG rendering)."""

    subject: SubjectModel = Field(description="Natal subject.")
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.", examples=["2025-05-01T00:00:00+00:00"])
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. 'next' (default) finds the upcoming crossing; 'previous' finds the most recent past crossing. Seeded with the instant of a crossing this API reported, 'next' yields the following crossing and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution crossing instants are reported at. Requires the libephemeris backend."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay for dual wheels.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "LunarNodeCrossingRequestModel":
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self


class LunarNodeCrossingDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for lunar node crossing data (no SVG)."""

    subject: SubjectModel = Field(description="Natal subject.")
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.")
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. 'next' (default) finds the upcoming crossing; 'previous' finds the most recent past crossing. Seeded with the instant of a crossing this API reported, 'next' yields the following crossing and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution crossing instants are reported at. Requires the libephemeris backend."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "LunarNodeCrossingDataRequestModel":
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self


class HeliocentricReturnContextRequestModel(ChartDataConfigurationMixin):
    """Request payload for heliocentric return AI context.

    Supports two modes:
    - **Compute mode**: provide ``subject`` + ``planet`` + ``year``/``iso_datetime``.
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    subject: Optional[SubjectModel] = Field(default=None, description="Natal subject. Required when chart_data is not provided.")
    planet: Optional[str] = Field(default=None, description="Planet whose heliocentric return to compute (required in compute mode).", examples=["Mars"])
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.")
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. Seeded with the instant of a return this API reported, 'next' yields the following return and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution return instants are reported at. Requires the libephemeris backend for backward search."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay for dual wheels.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Pre-computed chart data object. When provided, the endpoint skips calculation and generates context directly.",
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "HeliocentricReturnContextRequestModel":
        if self.chart_data is not None:
            return self
        if self.subject is None:
            raise ValueError("Provide either 'chart_data' (pre-computed) or 'subject' with search parameters.")
        if self.planet is None:
            raise ValueError("'planet' is required when computing a heliocentric return.")
        # Canonicalize case/aliases ('mars' -> 'Mars') — kerykeion's planet
        # lookup is exact-match and would reject the raw name with a 400.
        self.planet = _normalize_point_name(self.planet)
        if self.planet in LUNAR_DERIVED_POINTS:
            raise ValueError(f"Heliocentric returns are undefined for lunar-derived point '{self.planet}'. Use a planet with its own heliocentric orbit (e.g. 'Mars', 'Jupiter').")
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self


class LunarNodeCrossingContextRequestModel(ChartDataConfigurationMixin):
    """Request payload for lunar node crossing AI context.

    Supports two modes:
    - **Compute mode**: provide ``subject`` + ``year``/``iso_datetime``.
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    subject: Optional[SubjectModel] = Field(default=None, description="Natal subject. Required when chart_data is not provided.")
    year: Optional[int] = Field(default=None, ge=-13200, le=9999, description="Year to search from (astronomical numbering: 0 = 1 BCE).")
    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime to search from.")
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction. Seeded with the instant of a crossing this API reported, 'next' yields the following crossing and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution crossing instants are reported at. Requires the libephemeris backend for backward search."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(default="dual", description="Wheel configuration.")
    include_house_comparison: bool = Field(default=True, description="Include house overlay for dual wheels.")
    return_location: Optional[ReturnLocationModel] = Field(default=None, description="Override return location.")
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Pre-computed chart data object. When provided, the endpoint skips calculation and generates context directly.",
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "LunarNodeCrossingContextRequestModel":
        if self.chart_data is not None:
            return self
        if self.subject is None:
            raise ValueError("Provide either 'chart_data' (pre-computed) or 'subject' with search parameters.")
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year'.")
        if self.wheel_type == "single":
            self.include_house_comparison = False
        return self
