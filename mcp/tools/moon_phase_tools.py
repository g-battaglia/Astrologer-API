"""MCP tools for moon phase calculations."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from pydantic import Field

from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

from ...utils.clock import utc_now
from ...utils.router_utils import moon_phase_context_payload, moon_phase_payload, run_heavy

logger = logging.getLogger(__name__)


def register_moon_phase_tools(mcp: Any) -> None:
    """Register moon phase MCP tools on the given FastMCP server instance."""

    @mcp.tool()
    async def get_moon_phase(
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        latitude: Annotated[float, Field(ge=-90, le=90)],
        longitude: Annotated[float, Field(ge=-180, le=180)],
        timezone: str,
        second: int = 0,
        using_default_location: bool = False,
        location_precision: Annotated[int, Field(ge=0, le=10)] = 0,
        include_ai_context: bool = True,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Get detailed moon phase information for a specific date, time, and location.

        Returns phase name, illumination percentage, stage (waxing/waning), lunar age,
        upcoming major phases, next eclipses, sunrise/sunset, and zodiac positions.
        ``location_precision`` rounds the returned coordinates; ``using_default_location``
        substitutes the library's default observation point.
        """
        try:
            subject = await run_heavy(
                AstrologicalSubjectFactory.from_birth_data,
                name="Moon Phase",
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                seconds=second,
                city="",
                nation="GB",
                lng=longitude,
                lat=latitude,
                tz_str=timezone,
                online=False,
                active_points=list(DEFAULT_ACTIVE_POINTS),
                suppress_geonames_warning=True,
            )

            overview = await run_heavy(
                MoonPhaseDetailsFactory.from_subject,
                subject,
                using_default_location=using_default_location,
                location_precision=location_precision,
            )

            if include_ai_context:
                return await run_heavy(moon_phase_context_payload, overview, omit_nulls=omit_nulls)
            return await run_heavy(moon_phase_payload, overview, omit_nulls=omit_nulls)

        except Exception as exc:
            logger.error("get_moon_phase failed | exception=%s", type(exc).__name__)
            raise

    @mcp.tool()
    async def get_current_moon_phase(
        using_default_location: bool = True,
        location_precision: Annotated[int, Field(ge=0, le=10)] = 0,
        include_ai_context: bool = True,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Get detailed moon phase information for the current UTC moment at Greenwich.

        Uses real-time UTC and Greenwich Observatory coordinates. Returns phase name,
        illumination, stage, lunar age, upcoming phases, and eclipses.
        ``location_precision`` rounds the returned coordinates; ``using_default_location``
        substitutes the library's default observation point.
        """
        try:
            now_utc = utc_now()

            subject = await run_heavy(
                AstrologicalSubjectFactory.from_birth_data,
                name="Moon Phase",
                year=now_utc.year,
                month=now_utc.month,
                day=now_utc.day,
                hour=now_utc.hour,
                minute=now_utc.minute,
                seconds=now_utc.second,
                city="Greenwich",
                nation="GB",
                lng=-0.001545,
                lat=51.477928,
                tz_str="Etc/UTC",
                online=False,
                active_points=list(DEFAULT_ACTIVE_POINTS),
                suppress_geonames_warning=True,
            )

            overview = await run_heavy(
                MoonPhaseDetailsFactory.from_subject,
                subject,
                using_default_location=using_default_location,
                location_precision=location_precision,
            )

            if include_ai_context:
                return await run_heavy(moon_phase_context_payload, overview, omit_nulls=omit_nulls)
            return await run_heavy(moon_phase_payload, overview, omit_nulls=omit_nulls)

        except Exception as exc:
            logger.error("get_current_moon_phase failed | exception=%s", type(exc).__name__)
            raise
