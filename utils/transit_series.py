"""Shared construction and validation for REST and MCP transit time series."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from kerykeion import EphemerisDataFactory, TransitsTimeRangeFactory
from kerykeion.schemas import KerykeionException
from kerykeion.utilities import localize_naive

from ..types.request_models import EPHEMERIS_MAX_POINTS, _count_ephemeris_samples


MAX_TRANSIT_SCAN_DAYS = 1827
MAX_TRANSIT_SAMPLES = 10_000


def validate_transit_range(
    start_date: str,
    end_date: str,
    *,
    timezone_name: str,
    is_dst: bool | None,
    step_type: Literal["days", "hours", "minutes"],
    step: int,
) -> int:
    """Validate the shared range contract and return the inclusive sample count."""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        local_timezone = ZoneInfo(timezone_name)

        def to_utc(value: datetime) -> datetime:
            if value.tzinfo is None:
                return localize_naive(value, local_timezone, is_dst=is_dst).astimezone(timezone.utc)
            return value.astimezone(timezone.utc)

        start_comparable = to_utc(start)
        end_comparable = to_utc(end)
    except KerykeionException as exc:
        raise ValueError(
            "start_date/end_date contains an ambiguous or nonexistent local "
            "time in the requested timezone. Pass is_dst=true or is_dst=false "
            "to disambiguate it, or shift the timestamp outside the DST transition."
        ) from exc
    except ValueError as exc:
        raise ValueError(f"start_date/end_date must be ISO dates: {exc}") from exc
    except OverflowError as exc:
        raise ValueError("start_date/end_date is out of the supported range.") from exc

    if end_comparable <= start_comparable:
        raise ValueError("end_date must be after start_date.")
    if (end_comparable - start_comparable).days > MAX_TRANSIT_SCAN_DAYS:
        raise ValueError(f"Range too large; maximum span is {MAX_TRANSIT_SCAN_DAYS} days (~5 years).")
    samples = _count_ephemeris_samples(
        start_date,
        end_date,
        timezone_name=timezone_name,
        is_dst=is_dst,
        step_type=step_type,
        step=step,
    )
    if samples > MAX_TRANSIT_SAMPLES:
        raise ValueError(
            f"Range too large: {samples} transit samples requested (max {MAX_TRANSIT_SAMPLES}). "
            "Reduce the span or increase the step."
        )
    return samples


def transit_range_error(
    start_date: str,
    end_date: str,
    *,
    timezone_name: str,
    is_dst: bool | None,
    step_type: Literal["days", "hours", "minutes"],
    step: int,
) -> dict[str, str] | None:
    """MCP-compatible validation result for direct-call compatibility."""
    try:
        validate_transit_range(
            start_date,
            end_date,
            timezone_name=timezone_name,
            is_dst=is_dst,
            step_type=step_type,
            step=step,
        )
    except (ValueError, OverflowError) as exc:
        return {"status": "ERROR", "message": str(exc)}
    return None


def build_transit_series_factory(
    *,
    start_date: str,
    end_date: str,
    step_type: Literal["days", "hours", "minutes"],
    step: int,
    subject_request: Any,
    natal_subject: Any,
    active_points: list[str],
    calculate_dignities: bool = False,
) -> EphemerisDataFactory:
    """Build the identical ephemeris series for REST and MCP transit scans."""
    validate_transit_range(
        start_date,
        end_date,
        timezone_name=natal_subject.tz_str,
        is_dst=getattr(subject_request, "is_dst", None),
        step_type=step_type,
        step=step,
    )
    optional_kwargs: dict[str, Any] = {}
    if calculate_dignities and "calculate_dignities" in inspect.signature(EphemerisDataFactory).parameters:
        optional_kwargs["calculate_dignities"] = True
    return EphemerisDataFactory(
        start_datetime=datetime.fromisoformat(start_date),
        end_datetime=datetime.fromisoformat(end_date),
        step_type=step_type,
        step=step,
        lat=natal_subject.lat,
        lng=natal_subject.lng,
        tz_str=natal_subject.tz_str,
        zodiac_type=natal_subject.zodiac_type,
        sidereal_mode=natal_subject.sidereal_mode,
        houses_system_identifier=natal_subject.houses_system_identifier,
        perspective_type=natal_subject.perspective_type,
        custom_ayanamsa_t0=getattr(subject_request, "custom_ayanamsa_t0", None),
        custom_ayanamsa_ayan_t0=getattr(subject_request, "custom_ayanamsa_ayan_t0", None),
        active_points=cast(Any, list(active_points)),
        max_days=EPHEMERIS_MAX_POINTS,
        max_hours=EPHEMERIS_MAX_POINTS,
        max_minutes=EPHEMERIS_MAX_POINTS,
        **optional_kwargs,
    )


def transit_subjects_supported() -> bool:
    return "include_subjects" in inspect.signature(TransitsTimeRangeFactory.get_transit_moments).parameters
