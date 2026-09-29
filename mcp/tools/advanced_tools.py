"""MCP tools for advanced astrological features (28 tools)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Literal, Optional, cast
from zoneinfo import ZoneInfo

from kerykeion import (
    AspectsFactory,
    AstrologicalSubjectFactory,
    AstroCartographyFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    DominantsFactory,
    EclipseFactory,
    EphemerisDataFactory,
    FixedStarDiscoveryFactory,
    LunationFinderFactory,
    MidpointFactory,
    PlanetaryHoursFactory,
    PlanetaryNodesFactory,
    PlanetaryPhenomenaFactory,
    PrimaryDirectionsFactory,
    RelocatedChartFactory,
    ReportGenerator,
    RetrogradeStationFactory,
    SecondaryProgressionFactory,
    SignIngressFactory,
    SolarArcFactory,
    SunTimesFactory,
    TransitsTimeRangeFactory,
    VoidOfCourseMoonFactory,
    ZodiacalReleasingFactory,
    ProfectionsFactory,
    FirdariaFactory,
    HoraryIndicatorsFactory,
)

from pydantic import Field
from typing_extensions import Annotated

from ...types.request_models import HELIACAL_MAX_EVENT_WORK, MAX_HELIACAL_PLANETS
from ...utils.occultation import HELIACAL_SEARCH_TIMEOUT_S, OCCULTATION_PLANET_IDS, run_heliacal_search, run_occultation_search
from ...utils.subject_kwargs import subject_factory_kwargs
from ...utils.transit_series import build_transit_series_factory, transit_range_error, transit_subjects_supported
from ...utils.router_utils import (
    chart_data_payload,
    chart_payload,
    context_payload,
    dump,
    normalize_coordinate,
    resolve_nation,
    run_heavy,
)

# REST payload reshapers shared with the routers so MCP and REST emit
# identical shapes (moon-voc, sun-times, planetary-hours parity).
from ...utils.astronomy_payloads import _moon_voc_payload, _planetary_hours_payload, _sun_times_payload
from .core_tools import (
    _build_subject_from_model,
    _build_return_factory_from_model,
    _resolve_active_points,
    _resolve_active_aspects,
    _chart_data_kwargs,
    _v6_kwargs_from_model,
)
from ..types import MCPSubjectInput, MCPReturnLocationInput, MCPSolarPhaseThresholdsInput

logger = logging.getLogger(__name__)

# Caps shared with the REST request models (request_models.py) — MCP tools
# bypass those models, so the same limits are enforced here.
MAX_TRANSIT_BATCH_STEPS = 366
MAX_EPHEMERIS_POINTS = 20000
# Lunation / retrograde-station / sign-ingress finders share this cap with the
# REST request models (request_models.py: ~10 years).
MAX_FINDER_SCAN_DAYS = 3660


def _strip_nulls(value: Any) -> Any:
    """Recursively drop ``None`` values from dicts/lists.

    The REST reshapers (``_moon_voc_payload``, ``_sun_times_payload``,
    ``_planetary_hours_payload``) keep explicit nulls; this applies the MCP
    ``omit_nulls`` convention on top of their output without changing shapes.
    """
    if isinstance(value, dict):
        return {k: _strip_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_nulls(v) for v in value]
    return value


def _validate_iso_range(start_date: str, end_date: str) -> "Optional[dict[str, Any]]":
    """Validate an ISO date(time) range the way the REST finder request models do.

    A date-only ``end_date`` means "through the end of that UTC day". Returns an
    error payload (dict) on failure, or ``None`` when the range is valid.
    """
    from datetime import timezone

    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError as exc:
        return {"status": "ERROR", "message": f"start_date/end_date must be ISO dates: {exc}"}
    try:
        if start.tzinfo is not None:
            start = start.astimezone(timezone.utc).replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.astimezone(timezone.utc).replace(tzinfo=None)
    except OverflowError:
        return {"status": "ERROR", "message": "start_date/end_date is out of the supported range."}
    if "T" not in end_date and "t" not in end_date and " " not in end_date:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    if end <= start:
        return {"status": "ERROR", "message": "end_date must be after start_date."}
    if (end - start).days > MAX_FINDER_SCAN_DAYS:
        return {"status": "ERROR", "message": "Range too large; maximum span is ~10 years."}
    return None


def register_advanced_tools(mcp: Any) -> None:
    """Register all 17 advanced astrological MCP tools on the given FastMCP server instance."""

    # -----------------------------------------------------------------------
    # 1. Eclipses
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_eclipses(
        latitude: Annotated[Optional[float], Field(ge=-90, le=90)] = None,
        longitude: Annotated[Optional[float], Field(ge=-180, le=180)] = None,
        start_year: Annotated[int, Field(ge=-13200, le=9999)] = 2025,
        count: Annotated[int, Field(ge=1, le=50)] = 5,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Search for upcoming solar and lunar eclipses.

        Provide latitude and longitude for location-specific results, or omit both
        for a global search. For global searches, magnitude and obscuration are null
        (these require a specific location to compute).
        """
        try:
            if (latitude is None) != (longitude is None):
                return {
                    "status": "ERROR",
                    "message": "Provide both latitude and longitude for a local search, or omit both for a global search.",
                }
            is_global = latitude is None
            if not is_global:
                result = await run_heavy(
                    EclipseFactory.search_from_location,
                    lat=latitude,
                    lng=longitude,
                    start_year=start_year,
                    count=count,
                )
            else:
                result = await run_heavy(
                    EclipseFactory.search_global,
                    start_year=start_year,
                    count=count,
                )

            solar = dump(result.solar_eclipses, omit_nulls=omit_nulls)
            lunar = dump(result.lunar_eclipses, omit_nulls=omit_nulls)

            # Global search returns 0.0 for location-specific fields — replace with null
            if is_global:
                for event_list in (solar, lunar):
                    if isinstance(event_list, list):
                        for event in event_list:
                            if isinstance(event, dict):
                                for field in ("magnitude", "obscuration", "sun_altitude"):
                                    if field in event and event[field] == 0.0:
                                        event[field] = None

            return {
                "status": "OK",
                "solar_eclipses": solar,
                "lunar_eclipses": lunar,
                # REST parity (/api/v6/events/eclipses): echo the search
                # location (null for a global search).
                "latitude": getattr(result, "latitude", latitude),
                "longitude": getattr(result, "longitude", longitude),
            }

        except Exception as exc:
            logger.error("get_eclipses failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 2. Planetary Phenomena
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_planetary_phenomena(
        subject: MCPSubjectInput,
        planets: Optional[list[str]] = None,
        solar_phase_thresholds: Optional[MCPSolarPhaseThresholdsInput] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute observational phenomena for planets at a given moment.

        Returns phase angle, elongation, magnitude, and morning/evening star status.
        Each entry also carries its `solar_phase` — cazimi (within 17 arcminutes),
        combust (within 8°30'), under_the_beams (within 17°) or free — and
        `solar_phase_thresholds` echoes the half-widths that produced it, so the
        classification can be checked against the elongation it came from.
        Pass `solar_phase_thresholds` to widen or narrow those bands.
        The subject dict must include name, year, month, day, hour, minute, city, nation,
        and optionally latitude, longitude, timezone, and other subject fields.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            # Held back unless the caller sent it (REST parity,
            # the domain REST routers): an engine that predates the keyword
            # answers an unknown kwarg with a TypeError, i.e. a dead tool
            # rather than an ignored option.
            extra_kwargs: dict[str, Any] = {}
            if solar_phase_thresholds is not None:
                from kerykeion.schemas import SolarPhaseThresholdsModel

                extra_kwargs["solar_phase_thresholds"] = SolarPhaseThresholdsModel(**solar_phase_thresholds.model_dump())
            result = await run_heavy(
                PlanetaryPhenomenaFactory.from_subject,
                subj,
                planets=planets,
                **extra_kwargs,
            )

            thresholds = getattr(result, "solar_phase_thresholds", None)
            return {
                "status": "OK",
                "phenomena": dump(result.phenomena, omit_nulls=omit_nulls),
                "solar_phase_thresholds": dump(thresholds) if thresholds is not None else None,
                "iso_datetime": getattr(result, "iso_datetime", None),
                "julian_day": getattr(result, "julian_day", None),
            }

        except Exception as exc:
            logger.error("get_planetary_phenomena failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 3. Planetary Nodes
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_planetary_nodes(
        subject: MCPSubjectInput,
        method: Literal["mean", "osculating"] = "mean",
        planets: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute ascending/descending nodes and perihelion/aphelion for planets.

        Method can be 'mean' (averaged over time) or 'osculating' (instantaneous).
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                PlanetaryNodesFactory.from_subject,
                subj,
                method=method,
                planets=planets,
            )

            return {
                "status": "OK",
                "nodes": dump(result.nodes, omit_nulls=omit_nulls),
                "method": method,
                "iso_datetime": getattr(result, "iso_datetime", None),
                "julian_day": getattr(result, "julian_day", None),
            }

        except Exception as exc:
            logger.error("get_planetary_nodes failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 4. Heliacal Events
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_heliacal_events(
        subject: MCPSubjectInput,
        count: Annotated[int, Field(ge=1, le=20)] = 5,
        planets: Annotated[Optional[list[str]], Field(max_length=MAX_HELIACAL_PLANETS)] = None,
        event_types: Optional[list[Literal["heliacal_rising", "heliacal_setting", "evening_first", "morning_last"]]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Search for heliacal rising/setting events (first/last visibility).

        Finds when planets and stars first become visible or disappear near the horizon
        at the subject's observation location. ``event_types`` selects which events to
        search (defaults to heliacal rising + setting); the other two are the evening
        first and morning last appearances.
        """
        try:
            event_type_count = len(event_types) if event_types else 2
            work = count * event_type_count
            if work > HELIACAL_MAX_EVENT_WORK:
                return {
                    "status": "ERROR",
                    "message": (
                        f"Heliacal search costs {work} event-type units "
                        f"(count × event_types; max {HELIACAL_MAX_EVENT_WORK}). "
                        "Reduce count or event_types."
                    ),
                }

            resolved_event_types = None
            if event_types:
                label_to_int = {
                    "heliacal_rising": 1,
                    "heliacal_setting": 2,
                    "evening_first": 3,
                    "morning_last": 4,
                }
                resolved_event_types = [label_to_int[e] for e in event_types]
            events = await run_heliacal_search(
                timeout=HELIACAL_SEARCH_TIMEOUT_S,
                subject_kwargs=subject_factory_kwargs(subject),
                count=count,
                planets=planets,
                event_types=resolved_event_types,
            )

            return {"status": "OK", "events": dump(events, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_heliacal_events failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 5. Occultations
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_occultations(
        subject: MCPSubjectInput,
        planet: Literal["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"] = "Venus",
        count: Annotated[int, Field(ge=1, le=50)] = 5,
        global_search: bool = False,
        timeout: float = 30.0,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Search for lunar occultations of a planet (the Moon passes in front of it).

        Set global_search=True for worldwide events, or False for events visible
        from the subject's location. Timeout controls how long to wait (default 30s).
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)

            planet_id = OCCULTATION_PLANET_IDS[planet]

            events = await run_occultation_search(
                "global" if global_search else "local",
                timeout=max(1.0, min(timeout, 120.0)),
                julian_day=subj.julian_day,
                planet_id=planet_id,
                count=count,
                **({} if global_search else {"lat": subj.lat, "lng": subj.lng}),
            )

            return {"status": "OK", "events": dump(events, omit_nulls=omit_nulls)}

        except TimeoutError:
            return {
                "status": "ERROR",
                "message": f"Occultation search timed out after {timeout}s. Try reducing 'count' or narrowing the search.",
            }
        except Exception as exc:
            logger.error("get_occultations failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 6. Relocated Chart
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_relocated_chart(
        subject: MCPSubjectInput,
        new_latitude: float,
        new_longitude: float,
        new_city: str = "Relocated",
        new_nation: str = "",
        new_timezone: Optional[str] = None,
        active_points: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Relocate a natal chart to a new geographic location.

        Preserves original planetary positions but recalculates houses and angles
        for the new location.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject, active_points=_resolve_active_points(active_points))
            relocated = await run_heavy(
                RelocatedChartFactory.relocate,
                subj,
                new_lat=new_latitude,
                new_lng=new_longitude,
                new_city=new_city,
                new_nation=new_nation,
                new_tz_str=new_timezone,
            )

            return {"status": "OK", "subject": dump(relocated, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_relocated_chart failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 7. Fixed Star Conjunctions
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_fixed_star_conjunctions(
        subject: MCPSubjectInput,
        orb: float = 1.0,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Discover prominent fixed stars in conjunction with chart points.

        Searches for fixed stars within the specified orb of the subject's
        planetary and angle positions.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            stars = await run_heavy(FixedStarDiscoveryFactory.find_prominent_stars, subj, orb=orb)

            return {"status": "OK", "stars": dump(stars, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_fixed_star_conjunctions failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 8. Primary Directions
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_primary_directions(
        subject: MCPSubjectInput,
        max_years: Annotated[float, Field(ge=1, le=200)] = 100,
        rate_key: Literal["ptolemy", "naibod"] = "ptolemy",
        aspects: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute primary directions using the Placidus semi-arc method.

        Returns both the list of directed aspects and the speculum table with
        right ascension, declination, and semi-arc data.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            directions = await run_heavy(
                PrimaryDirectionsFactory.compute,
                subj,
                max_years=max_years,
                rate_key=rate_key,
                aspects=aspects,
            )
            speculum = await run_heavy(PrimaryDirectionsFactory.compute_speculum, subj)

            return {
                "status": "OK",
                "directions": dump(directions, omit_nulls=omit_nulls),
                "speculum": dump(speculum, omit_nulls=omit_nulls),
            }

        except Exception as exc:
            logger.error("get_primary_directions failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 9. Astro-Cartography
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_astro_cartography(
        subject: MCPSubjectInput,
        step: float = 1.0,
        tolerance: Optional[float] = None,
        lat_range_min: float = -66,
        lat_range_max: float = 66,
        planets: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute astro-cartography (ACG) planetary lines.

        Shows where planets cross ASC/DSC/MC/IC lines on the Earth's surface.
        Returns coordinate points for each line that can be plotted on a map.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)

            kwargs: dict[str, Any] = {
                "step": step,
                "lat_range": (lat_range_min, lat_range_max),
            }
            if tolerance is not None:
                kwargs["tolerance"] = tolerance
            if planets is not None:
                kwargs["planets"] = planets

            lines = await run_heavy(AstroCartographyFactory.compute, subj, **kwargs)

            return {"status": "OK", "lines": dump(lines, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_astro_cartography failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 10. Declination Aspects
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_declination_aspects(
        subject: MCPSubjectInput,
        second_subject: Optional[MCPSubjectInput] = None,
        active_points: Optional[list[str]] = None,
        orb: float = 1.0,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute declination aspects (parallel / contra-parallel).

        For a single chart, finds declination aspects between the subject's own points.
        When second_subject is provided, computes cross-chart declination aspects.
        """
        try:
            pts = _resolve_active_points(active_points)
            subj1 = await run_heavy(_build_subject_from_model, subject, active_points=pts)

            if second_subject:
                subj2 = await run_heavy(_build_subject_from_model, second_subject, active_points=pts)
                aspects = await run_heavy(
                    AspectsFactory.dual_chart_declination_aspects,
                    subj1,
                    subj2,
                    active_points=pts,
                    orb=orb,
                )
            else:
                aspects = await run_heavy(
                    AspectsFactory.single_chart_declination_aspects,
                    subj1,
                    active_points=pts,
                    orb=orb,
                )

            return {"status": "OK", "aspects": dump(aspects, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_declination_aspects failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 11. Transit Events
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_transit_events(
        subject: MCPSubjectInput,
        start_date: str,
        end_date: str,
        step_days: Annotated[int, Field(ge=1, le=30)] = 1,
        step_type: Literal["days", "hours", "minutes"] = "days",
        refine_exact_moments: bool = False,
        refinement_iterations: Annotated[int, Field(ge=1, le=30)] = 12,
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        axis_orb_limit: Optional[float] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute transit events over a time range.

        Identifies when transiting planets form aspects to natal positions.
        Enable refine_exact_moments to refine exact aspect timing (ternary
        search); precision follows refinement_iterations — at daily sampling
        the default 12 lands within a few minutes and 30 reaches sub-second.
        Dates should be ISO format (e.g. '2025-01-01').

        Note: exact_moment may be null when refine_exact_moments is False (default).
        applying/separating timestamps may be null when the aspect boundary falls
        outside the searched date range.
        """
        try:
            pts = _resolve_active_points(active_points)
            asps = _resolve_active_aspects(active_aspects)

            range_error = transit_range_error(
                start_date,
                end_date,
                timezone_name=subject.timezone or "Etc/UTC",
                is_dst=subject.is_dst,
                step_type=step_type,
                step=step_days,
            )
            if range_error is not None:
                return range_error

            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=pts)

            ephemeris_factory = build_transit_series_factory(
                start_date=start_date,
                end_date=end_date,
                step_type=step_type,
                step=step_days,
                subject_request=subject,
                natal_subject=natal_subject,
                active_points=pts,
            )
            ephemeris_points = await run_heavy(ephemeris_factory.get_ephemeris_data_as_astrological_subjects)

            transits_factory = TransitsTimeRangeFactory(
                natal_chart=natal_subject,
                ephemeris_data_points=ephemeris_points,
                active_points=pts,
                active_aspects=asps,
                axis_orb_limit=axis_orb_limit,
            )

            result = await run_heavy(
                transits_factory.get_transit_events,
                refine_exact_moments=refine_exact_moments,
                refinement_iterations=refinement_iterations,
            )

            return {
                "status": "OK",
                "events": dump(result.events, omit_nulls=omit_nulls),
                "subject": dump(result.subject, omit_nulls=omit_nulls),
            }

        except Exception as exc:
            logger.error("get_transit_events failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 12. Transit Moments
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_transit_moments(
        subject: MCPSubjectInput,
        start_date: str,
        end_date: str,
        step_days: Annotated[int, Field(ge=1, le=30)] = 1,
        step_type: Literal["days", "hours", "minutes"] = "days",
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        axis_orb_limit: Optional[float] = None,
        include_transit_subjects: bool = False,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute transit moment snapshots over a date range.

        For each date in the range, returns all active aspects between transiting
        planets and natal positions. Dates should be ISO format (e.g. '2025-01-01').
        """
        try:
            pts = _resolve_active_points(active_points)
            asps = _resolve_active_aspects(active_aspects)

            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=pts)

            if include_transit_subjects and not transit_subjects_supported():
                return {
                    "status": "ERROR",
                    "message": "The installed engine does not support include_transit_subjects.",
                    "error_type": "TransitSubjectsUnsupportedError",
                }

            ephemeris_factory = build_transit_series_factory(
                start_date=start_date,
                end_date=end_date,
                step_type=step_type,
                step=step_days,
                subject_request=subject,
                natal_subject=natal_subject,
                active_points=pts,
                calculate_dignities=include_transit_subjects and subject.calculate_dignities,
            )
            ephemeris_points = await run_heavy(ephemeris_factory.get_ephemeris_data_as_astrological_subjects)

            transits_factory = TransitsTimeRangeFactory(
                natal_chart=natal_subject,
                ephemeris_data_points=ephemeris_points,
                active_points=pts,
                active_aspects=asps,
                axis_orb_limit=axis_orb_limit,
            )

            moments_kwargs = {"include_subjects": True} if include_transit_subjects else {}
            result = await run_heavy(transits_factory.get_transit_moments, **moments_kwargs)
            transits = cast(list[dict[str, Any]], dump(result.transits, omit_nulls=omit_nulls))
            if not include_transit_subjects:
                for snapshot in transits:
                    snapshot.pop("subject", None)

            return {
                "status": "OK",
                "transits": transits,
                "subject": dump(result.subject, omit_nulls=omit_nulls),
                "dates": result.dates,
            }

        except Exception as exc:
            logger.error("get_transit_moments failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 13. Ephemeris
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_ephemeris(
        start_date: str,
        end_date: str,
        step_type: Literal["days", "hours", "minutes"] = "days",
        step: Annotated[int, Field(ge=1)] = 1,
        latitude: float = 51.4769,
        longitude: float = 0.0005,
        timezone: str = "Etc/UTC",
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        houses_system_identifier: str = "P",
        perspective_type: str = "Apparent Geocentric",
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
        is_dst: Optional[bool] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Generate an ephemeris table with planetary positions and house cusps.

        Computes positions over a date range at configurable intervals.
        step_type can be 'days', 'hours', or 'minutes'.
        Dates should be ISO format (e.g. '2025-01-01').
        For sidereal_mode='USER' the custom_ayanamsa_t0/custom_ayanamsa_ayan_t0
        pair is required.
        """
        try:
            if sidereal_mode == "USER" and (custom_ayanamsa_t0 is None or custom_ayanamsa_ayan_t0 is None):
                return {
                    "status": "ERROR",
                    "message": "custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are required when sidereal_mode='USER'.",
                }
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            if end_dt <= start_dt:
                return {"status": "ERROR", "message": "end_date must be after start_date."}
            unit_seconds = {"days": 86400, "hours": 3600, "minutes": 60}[step_type]
            # +1: the factory counts both endpoints (span//step + 1 samples);
            # matching its fencepost keeps the tool's own cap message authoritative.
            points = (end_dt - start_dt).total_seconds() / (unit_seconds * step) + 1
            if points > MAX_EPHEMERIS_POINTS:
                return {
                    "status": "ERROR",
                    "message": (f"Range too large: ~{int(points)} ephemeris points requested (max {MAX_EPHEMERIS_POINTS}). Reduce the date span or increase the step."),
                }

            factory = EphemerisDataFactory(
                start_datetime=start_dt,
                end_datetime=end_dt,
                step_type=step_type,
                step=step,
                lat=latitude,
                lng=longitude,
                tz_str=timezone,
                zodiac_type=zodiac_type,
                sidereal_mode=sidereal_mode,
                houses_system_identifier=houses_system_identifier,
                perspective_type=perspective_type,
                custom_ayanamsa_t0=custom_ayanamsa_t0,
                custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
                is_dst=is_dst if is_dst is not None else False,
                # Mirror the tool-level cap so the factory's own limits agree
                # with the points check above (REST parity: the REST router passes
                # EPHEMERIS_MAX_POINTS; kerykeion's defaults are 730/8760).
                max_days=MAX_EPHEMERIS_POINTS,
                max_hours=MAX_EPHEMERIS_POINTS,
                max_minutes=MAX_EPHEMERIS_POINTS,
            )

            data = await run_heavy(factory.get_ephemeris_data, as_model=True)

            return {"status": "OK", "ephemeris": dump(data, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_ephemeris failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 14. Report Generator
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def generate_report(
        subject: MCPSubjectInput,
        second_subject: Optional[MCPSubjectInput] = None,
        chart_type: Optional[Literal["Natal", "Synastry", "Transit", "Composite"]] = None,
        include_aspects: Optional[bool] = None,
        max_aspects: Annotated[Optional[int], Field(ge=1, le=100)] = None,
    ) -> dict[str, Any]:
        """Generate a human-readable text report for an astrological subject.

        Summarizes planetary placements, house positions, and optionally aspects.
        Three report kinds are reachable (REST /advanced/report parity):
        - Subject (default): pass only ``subject`` for a bare natal-subject report.
        - Single chart: pass ``chart_type='Natal'`` (or set ``include_aspects=true``)
          to build natal chart data so the aspect table is included.
        - Dual chart: pass ``chart_type`` in {'Synastry','Transit','Composite'} with
          ``second_subject`` for a relational report.
        ``max_aspects`` caps the aspect table length.
        """
        try:
            # REST parity (ReportRequestModel.validate_report_kind).
            dual = ("Synastry", "Transit", "Composite")
            if chart_type in dual and second_subject is None:
                return {"status": "ERROR", "message": f"second_subject is required when chart_type='{chart_type}'."}
            if second_subject is not None and chart_type not in dual:
                return {"status": "ERROR", "message": "second_subject requires chart_type in {'Synastry','Transit','Composite'}."}

            kwargs: dict[str, Any] = {}
            if include_aspects is not None:
                kwargs["include_aspects"] = include_aspects
            if max_aspects is not None:
                kwargs["max_aspects"] = max_aspects

            def _build_report_model():
                # Mirrors the REST /api/v6/reports handler: a bare
                # subject never renders an aspect table in kerykeion's
                # ReportGenerator, so chart data is built whenever aspects are
                # requested (or a chart_type is given).
                primary = _build_subject_from_model(subject)
                if chart_type in dual:
                    assert second_subject is not None  # guarded above
                    second = _build_subject_from_model(second_subject)
                    if chart_type == "Composite":
                        composite = CompositeSubjectFactory(primary, second).get_midpoint_composite_subject_model()
                        return ChartDataFactory.create_chart_data("Composite", composite)
                    return ChartDataFactory.create_chart_data(chart_type, primary, second)
                # Single-subject: build natal chart data when aspects are wanted so
                # the aspect table is populated; otherwise a bare subject report.
                if chart_type == "Natal" or include_aspects:
                    return ChartDataFactory.create_chart_data("Natal", primary)
                return primary

            model = await run_heavy(_build_report_model)
            generator = ReportGenerator(model)
            report_text = await run_heavy(generator.generate_report, **kwargs)

            return {"status": "OK", "report": report_text}

        except Exception as exc:
            logger.error("generate_report failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 15. Heliocentric Return
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_heliocentric_return(
        subject: MCPSubjectInput,
        planet: str,
        year: Optional[int] = None,
        iso_datetime: Optional[str] = None,
        direction: Literal["next", "previous"] = "next",
        wheel_type: Literal["dual", "single"] = "dual",
        return_location: Optional[MCPReturnLocationInput] = None,
        include_house_comparison: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering (only used when include_svg=True)
        theme: str = "classic",
        language: str = "EN",
        split_chart: bool = False,
        transparent_background: bool = False,
        show_house_position_comparison: bool = True,
        show_cusp_position_comparison: bool = True,
        show_degree_indicators: bool = True,
        show_aspect_icons: bool = True,
        custom_title: Optional[str] = None,
        style: str = "classic",
        glyph_size: str = "medium",
        show_zodiac_background_ring: bool = True,
        show_diurnality: bool = True,
        show_motion_state: bool = False,
        show_out_of_bounds: bool = False,
        show_aspect_movement: bool = False,
        show_relationship_score: bool = False,
        show_ayanamsa_value: bool = False,
        show_polar_fallback_note: bool = False,
        double_chart_aspect_grid_type: str = "list",
        auto_size: bool = True,
        padding: int = 20,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, Any]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute a heliocentric return chart for a given planet.

        The return occurs when the planet returns to its natal heliocentric longitude.
        Search from iso_datetime or year (Jan 1) when provided; otherwise from the
        birth moment. 'previous' searches backwards from the starting point.
        Supports dual-wheel (natal + return) or single-wheel (return only) display.
        """
        try:
            # REST parity (HeliocentricReturn*RequestModel): lunar-derived
            # points oscillate around Earth's orbit — their "heliocentric
            # return" is astronomically undefined, and kerykeion only rejects
            # Sun/Moon.
            from ...types.request_models import LUNAR_DERIVED_POINTS, _normalize_point_name

            # Canonicalize case/aliases ('mars' -> 'Mars') — kerykeion's
            # planet lookup is exact-match.
            planet = _normalize_point_name(planet)
            if planet in LUNAR_DERIVED_POINTS:
                return {
                    "status": "ERROR",
                    "message": (f"Heliocentric returns are undefined for lunar-derived point '{planet}'. Use a planet with its own heliocentric orbit (e.g. 'Mars', 'Jupiter')."),
                }

            pts = _resolve_active_points(active_points)
            asps = _resolve_active_aspects(active_aspects)
            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=pts)
            return_factory = await run_heavy(_build_return_factory_from_model, natal_subject, return_location, subject_input=subject)

            backwards = direction == "previous"
            if iso_datetime:
                return_subject = await run_heavy(
                    return_factory.next_heliocentric_return_from_iso_formatted_time,
                    planet_name=planet,
                    iso_formatted_time=iso_datetime,
                    backwards=backwards,
                )
            elif year is not None and not backwards:
                return_subject = await run_heavy(
                    return_factory.next_heliocentric_return_from_year,
                    planet_name=planet,
                    year=year,
                )
            elif year is not None:
                return_subject = await run_heavy(
                    return_factory.next_heliocentric_return_from_date,
                    planet_name=planet,
                    year=year,
                    month=1,
                    day=1,
                    backwards=True,
                )
            else:
                # The planet sits exactly at its natal heliocentric longitude at
                # the birth instant, so a crossing search anchored there converges
                # on that trivial root (the birth moment itself). Step one day off
                # the anchor — far below any heliocentric period (Mercury ≈ 88d),
                # so no real return can be skipped.
                start_jd = natal_subject.julian_day + (-1.0 if backwards else 1.0)
                return_subject = await run_heavy(
                    return_factory.next_heliocentric_return,
                    planet_name=planet,
                    start_jd=start_jd,
                    backwards=backwards,
                )

            # Route through create_chart_data (not the create_*_return_chart_data
            # convenience methods) so axis_orb_limit/point_orb_adjustments reach
            # the factory — the convenience methods don't accept axis_orb_limit on
            # a60. Mirrors REST _build_return_chart_data and MCP get_solar_return.
            return_kwargs = _chart_data_kwargs(
                active_points=pts,
                active_aspects=asps,
                axis_orb_limit=axis_orb_limit,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                distribution_method=distribution_method,
                custom_distribution_weights=custom_distribution_weights,
            )
            if wheel_type == "dual":
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "DualReturnChart",
                    natal_subject,
                    return_subject,
                    include_house_comparison=include_house_comparison,
                    **return_kwargs,
                )
            else:
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "SingleReturnChart",
                    return_subject,
                    **return_kwargs,
                )

            if include_svg:
                payload = await run_heavy(
                    chart_payload,
                    chart_data,
                    theme,
                    language,
                    split_chart,
                    transparent_background=transparent_background,
                    show_house_position_comparison=show_house_position_comparison,
                    show_cusp_position_comparison=show_cusp_position_comparison,
                    show_degree_indicators=show_degree_indicators,
                    show_aspect_icons=show_aspect_icons,
                    custom_title=custom_title,
                    style=style,
                    glyph_size=glyph_size,
                    show_zodiac_background_ring=show_zodiac_background_ring,
                    double_chart_aspect_grid_type=double_chart_aspect_grid_type,
                    auto_size=auto_size,
                    padding=padding,
                    show_diurnality=show_diurnality,
                    show_motion_state=show_motion_state,
                    show_out_of_bounds=show_out_of_bounds,
                    show_aspect_movement=show_aspect_movement,
                    show_relationship_score=show_relationship_score,
                    show_ayanamsa_value=show_ayanamsa_value,
                    show_polar_fallback_note=show_polar_fallback_note,
                    omit_nulls=omit_nulls,
                )
            elif include_ai_context:
                payload = await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)
            else:
                payload = await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)

            payload["return_type"] = "Heliocentric"
            payload["planet"] = planet
            payload["wheel_type"] = wheel_type
            return payload

        except Exception as exc:
            logger.error("get_heliocentric_return failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 16. Lunar Node Crossing
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_lunar_node_crossing(
        subject: MCPSubjectInput,
        year: Optional[int] = None,
        iso_datetime: Optional[str] = None,
        direction: Literal["next", "previous"] = "next",
        wheel_type: Literal["dual", "single"] = "dual",
        return_location: Optional[MCPReturnLocationInput] = None,
        include_house_comparison: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering (only used when include_svg=True)
        theme: str = "classic",
        language: str = "EN",
        split_chart: bool = False,
        transparent_background: bool = False,
        show_house_position_comparison: bool = True,
        show_cusp_position_comparison: bool = True,
        show_degree_indicators: bool = True,
        show_aspect_icons: bool = True,
        custom_title: Optional[str] = None,
        style: str = "classic",
        glyph_size: str = "medium",
        show_zodiac_background_ring: bool = True,
        show_diurnality: bool = True,
        show_motion_state: bool = False,
        show_out_of_bounds: bool = False,
        show_aspect_movement: bool = False,
        show_relationship_score: bool = False,
        show_ayanamsa_value: bool = False,
        show_polar_fallback_note: bool = False,
        double_chart_aspect_grid_type: str = "list",
        auto_size: bool = True,
        padding: int = 20,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, Any]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute the next lunar node crossing chart.

        Finds when the Moon crosses its own node (ecliptic latitude zero) and
        generates the corresponding chart data. Search from iso_datetime or
        year (Jan 1) when provided; otherwise from the birth moment.
        'previous' searches backwards. Supports dual or single wheel display.
        """
        try:
            pts = _resolve_active_points(active_points)
            asps = _resolve_active_aspects(active_aspects)
            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=pts)
            return_factory = await run_heavy(_build_return_factory_from_model, natal_subject, return_location, subject_input=subject)

            backwards = direction == "previous"
            if iso_datetime:
                return_subject = await run_heavy(
                    return_factory.next_lunar_node_crossing_from_iso_formatted_time,
                    iso_formatted_time=iso_datetime,
                    backwards=backwards,
                )
            elif year is not None and not backwards:
                return_subject = await run_heavy(
                    return_factory.next_lunar_node_crossing_from_year,
                    year=year,
                )
            elif year is not None:
                return_subject = await run_heavy(
                    return_factory.next_lunar_node_crossing_from_date,
                    year=year,
                    month=1,
                    day=1,
                    backwards=True,
                )
            else:
                return_subject = await run_heavy(
                    return_factory.next_lunar_node_crossing,
                    start_jd=natal_subject.julian_day,
                    backwards=backwards,
                )

            # Route through create_chart_data so axis_orb_limit/point_orb_adjustments
            # reach the factory (convenience methods don't accept axis_orb_limit on
            # a60). Mirrors REST _build_return_chart_data and MCP get_solar_return.
            return_kwargs = _chart_data_kwargs(
                active_points=pts,
                active_aspects=asps,
                axis_orb_limit=axis_orb_limit,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                distribution_method=distribution_method,
                custom_distribution_weights=custom_distribution_weights,
            )
            if wheel_type == "dual":
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "DualReturnChart",
                    natal_subject,
                    return_subject,
                    include_house_comparison=include_house_comparison,
                    **return_kwargs,
                )
            else:
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "SingleReturnChart",
                    return_subject,
                    **return_kwargs,
                )

            if include_svg:
                payload = await run_heavy(
                    chart_payload,
                    chart_data,
                    theme,
                    language,
                    split_chart,
                    transparent_background=transparent_background,
                    show_house_position_comparison=show_house_position_comparison,
                    show_cusp_position_comparison=show_cusp_position_comparison,
                    show_degree_indicators=show_degree_indicators,
                    show_aspect_icons=show_aspect_icons,
                    custom_title=custom_title,
                    style=style,
                    glyph_size=glyph_size,
                    show_zodiac_background_ring=show_zodiac_background_ring,
                    double_chart_aspect_grid_type=double_chart_aspect_grid_type,
                    auto_size=auto_size,
                    padding=padding,
                    show_diurnality=show_diurnality,
                    show_motion_state=show_motion_state,
                    show_out_of_bounds=show_out_of_bounds,
                    show_aspect_movement=show_aspect_movement,
                    show_relationship_score=show_relationship_score,
                    show_ayanamsa_value=show_ayanamsa_value,
                    show_polar_fallback_note=show_polar_fallback_note,
                    omit_nulls=omit_nulls,
                )
            elif include_ai_context:
                payload = await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)
            else:
                payload = await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)

            payload["return_type"] = "Lunar_Node_Crossing"
            payload["wheel_type"] = wheel_type
            return payload

        except Exception as exc:
            logger.error("get_lunar_node_crossing failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 17. Transit Batch
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_transit_batch(
        subject: MCPSubjectInput,
        start_date: str,
        end_date: str,
        step_days: Annotated[int, Field(ge=1, le=30)] = 1,
        # Transit location override (optional — defaults to natal location)
        transit_city: Optional[str] = None,
        transit_nation: Optional[str] = None,
        transit_latitude: Optional[float] = None,
        transit_longitude: Optional[float] = None,
        transit_timezone: Optional[str] = None,
        # Computation
        include_house_comparison: bool = True,
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, Any]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Batch transit calculation over a date range.

        Computes full transit chart data (positions, houses, aspects,
        distributions) for every date in the range, using the same logic
        as get_transit. Returns an array of per-day results.

        start_date / end_date must be ISO date strings (e.g. '2026-04-01').
        step_days controls the interval between dates (1-30).
        """
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            if end_dt < start_dt:
                return {"status": "ERROR", "message": "end_date must be on or after start_date."}
            # Defense in depth: schema already enforces ge=1, but a zero/negative
            # step here would loop forever.
            if step_days < 1:
                return {"status": "ERROR", "message": "step_days must be >= 1."}
            steps = (end_dt - start_dt).days // step_days + 1
            if steps > MAX_TRANSIT_BATCH_STEPS:
                return {
                    "status": "ERROR",
                    "message": (f"Range too large: {steps} transit computations requested (max {MAX_TRANSIT_BATCH_STEPS}). Reduce the date span or increase step_days."),
                }

            def _work() -> dict[str, Any]:
                pts = _resolve_active_points(active_points)
                asps = _resolve_active_aspects(active_aspects)
                natal_subject = _build_subject_from_model(subject, active_points=pts)

                step = timedelta(days=step_days)

                # Transit location: use override or natal
                t_city = transit_city or natal_subject.city
                t_nation = resolve_nation(transit_nation) if transit_nation else natal_subject.nation
                t_lng = normalize_coordinate(transit_longitude) if transit_longitude is not None else natal_subject.lng
                t_lat = normalize_coordinate(transit_latitude) if transit_latitude is not None else natal_subject.lat
                t_tz = transit_timezone or natal_subject.tz_str

                # v6 calc flags + USER custom-ayanamsa pair inherited from the
                # natal request so the transit ring matches get_transit (and a
                # sidereal 'USER' batch doesn't raise).
                v6_kwargs = _v6_kwargs_from_model(subject)

                results = []
                current = start_dt
                while current <= end_dt:
                    transit_sub = AstrologicalSubjectFactory.from_birth_data(
                        name="Transit",
                        year=current.year,
                        month=current.month,
                        day=current.day,
                        hour=12,
                        minute=0,
                        seconds=0,
                        city=t_city,
                        nation=t_nation,
                        lng=t_lng,
                        lat=t_lat,
                        tz_str=t_tz,
                        online=False,
                        zodiac_type=natal_subject.zodiac_type,
                        sidereal_mode=natal_subject.sidereal_mode,
                        houses_system_identifier=natal_subject.houses_system_identifier,
                        perspective_type=natal_subject.perspective_type,
                        active_points=pts,
                        suppress_geonames_warning=True,
                        custom_ayanamsa_t0=subject.custom_ayanamsa_t0,
                        custom_ayanamsa_ayan_t0=subject.custom_ayanamsa_ayan_t0,
                        **v6_kwargs,
                    )

                    # Route through create_chart_data (not create_transit_chart_data)
                    # so axis_orb_limit/point_orb_adjustments reach the factory —
                    # the convenience method doesn't accept axis_orb_limit on a60.
                    chart_data = ChartDataFactory.create_chart_data(
                        "Transit",
                        natal_subject,
                        transit_sub,
                        include_house_comparison=include_house_comparison,
                        **_chart_data_kwargs(
                            active_points=pts,
                            active_aspects=asps,
                            axis_orb_limit=axis_orb_limit,
                            point_orb_adjustments=point_orb_adjustments,
                            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                            distribution_method=distribution_method,
                            custom_distribution_weights=custom_distribution_weights,
                        ),
                    )

                    results.append(
                        {
                            "date": current.isoformat(),
                            "chart_data": dump(chart_data),
                        }
                    )
                    current += step

                return {"status": "OK", "results": results}

            return await run_heavy(_work)

        except Exception as exc:
            logger.error("get_transit_batch failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 18. Secondary Progressions
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_secondary_progressions(
        subject: MCPSubjectInput,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
        active_points: Optional[list[str]] = None,
        compute_aspects: bool = True,
        aspect_orb: float = 3.0,
        aspects: Optional[list[str]] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute the day-for-a-year secondary-progressed chart for a target moment.

        The progressed chart is calculated for ``birth + (target - birth) / 365.25``
        days at the natal location, reusing every natal setting. Pass exactly one of
        ``target_iso_utc_datetime`` or ``target_year``. The default 3 degree orb is the
        tight predictive standard.
        """
        try:
            if (target_iso_utc_datetime is None) == (target_year is None):
                return {"status": "ERROR", "message": "Provide exactly one of 'target_iso_utc_datetime' or 'target_year'."}

            if active_points:
                # Same alias/case canonicalization the REST models apply — raw
                # names like 'asc' would be silently dropped by the factories.
                active_points = _resolve_active_points(active_points)
            subj = await run_heavy(_build_subject_from_model, subject, active_points=active_points)
            result = await run_heavy(
                SecondaryProgressionFactory.compute_full,
                subj,
                target_iso_utc_datetime=target_iso_utc_datetime,
                target_year=target_year,
                active_points=active_points,
                compute_aspects=compute_aspects,
                aspect_orb=aspect_orb,
                aspects=aspects,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            )

            return {
                "status": "OK",
                "progressed_subject": dump(result.progressed_subject, omit_nulls=omit_nulls),
                "progressed_points": [p.model_dump() for p in result.progressed_points],
                "target_iso_utc_datetime": result.target_iso_utc_datetime,
                "ephemeris_iso_utc_datetime": result.ephemeris_iso_utc_datetime,
                "progressed_to_natal_aspects": dump(result.progressed_to_natal_aspects, omit_nulls=omit_nulls),
            }

        except Exception as exc:
            logger.error("get_secondary_progressions failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 19. Solar Arc Directions
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_solar_arc_directions(
        subject: MCPSubjectInput,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
        active_points: Optional[list[str]] = None,
        compute_aspects: bool = True,
        aspect_orb: float = 3.0,
        aspects: Optional[list[str]] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute solar arc directions for a target moment.

        The progressed Sun's longitude minus the natal Sun's longitude (shortest
        signed arc) is the solar arc; it is applied to every requested natal point.
        Pass exactly one of ``target_iso_utc_datetime`` or ``target_year``.
        """
        try:
            if (target_iso_utc_datetime is None) == (target_year is None):
                return {"status": "ERROR", "message": "Provide exactly one of 'target_iso_utc_datetime' or 'target_year'."}

            if active_points:
                # Same alias/case canonicalization the REST models apply — raw
                # names like 'asc' would be silently dropped by the factories.
                active_points = _resolve_active_points(active_points)
            subj = await run_heavy(_build_subject_from_model, subject, active_points=active_points)
            result = await run_heavy(
                SolarArcFactory.compute,
                subj,
                target_iso_utc_datetime=target_iso_utc_datetime,
                target_year=target_year,
                active_points=active_points,
                compute_aspects=compute_aspects,
                aspect_orb=aspect_orb,
                aspects=aspects,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            )

            return {"status": "OK", "solar_arc_subject": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_solar_arc_directions failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 20. Midpoints
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_midpoints(
        subject: MCPSubjectInput,
        active_points: Optional[list[str]] = None,
        aspect_orb: float = 1.0,
        aspects: Optional[list[str]] = None,
        compute_aspects: bool = True,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute the full midpoint table for a chart.

        Each midpoint reports its longitude on the shorter arc, sign + position,
        the 90 degree dial position (cosmobiology / Uranian), and the third points
        that aspect it within ``aspect_orb`` degrees. ``active_points`` selects the
        midpoint constituents (defaults to the standard 14-point set).
        """
        try:
            if active_points:
                # REST parity (MidpointsRequestModel): canonicalize aliases so
                # 'asc'/'mc' are not silently dropped by the constituent matcher.
                active_points = _resolve_active_points(active_points)
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                MidpointFactory.compute,
                subj,
                active_points=active_points,
                compute_aspects=compute_aspects,
                aspect_orb=aspect_orb,
                aspects=aspects,
            )

            return {"status": "OK", "midpoints": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_midpoints failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 21. Zodiacal Releasing
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_zodiacal_releasing(
        subject: MCPSubjectInput,
        lot: Literal["fortune", "spirit"] = "fortune",
        levels: Annotated[int, Field(ge=1, le=4)] = 2,
        target_date: Optional[str] = None,
        life_cap_years: Annotated[int, Field(ge=1, le=120)] = 100,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute zodiacal releasing (aphesis) from the Part of Fortune or Spirit.

        Periods unfold from the lot's sign in zodiacal order, each ruling for its
        general years and subdividing into months, days and finer levels.
        ``levels`` (1-4): L1/L2 are built in full; deeper levels only along the
        ``target_date`` path. ``life_cap_years`` bounds the L1 timeline projection.
        Requires a known birth time.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                ZodiacalReleasingFactory.from_subject,
                subj,
                lot=lot,
                levels=levels,
                target_date=target_date,
                life_cap_years=life_cap_years,
            )

            return {"status": "OK", "zodiacal_releasing": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_zodiacal_releasing failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 21b. Annual Profections
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_profections(
        subject: MCPSubjectInput,
        target_date: Optional[str] = None,
        years_before: Annotated[int, Field(ge=0, le=120)] = 3,
        years_after: Annotated[int, Field(ge=0, le=120)] = 4,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute annual profections — the Hellenistic year-lord technique.

        Each completed year of life activates one house counted from the
        Ascendant (age 0 = 1st house), cycling every twelve years; the Lord of
        the Year is the traditional ruler of the profected cusp's sign, in the
        subject's own house system. The age rolls on the birthday anniversary
        in the subject's timezone. ``target_date`` defaults to today there.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                ProfectionsFactory.from_subject,
                subj,
                target_date=target_date,
                years_before=years_before,
                years_after=years_after,
            )

            return {"status": "OK", "profections": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_profections failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 21c. Firdaria
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_firdaria(
        subject: MCPSubjectInput,
        target_date: Optional[str] = None,
        life_cap_years: Annotated[int, Field(ge=1, le=120)] = 120,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute the firdaria (Persian time-lord) periods.

        Day charts open with the Sun's period, night charts with the Moon's;
        the 75-year cycle repeats up to ``life_cap_years``. Planetary periods
        carry seven sub-periods opening with their own lord; node periods stay
        undivided. Requires a real sect: a midpoint composite is rejected.
        ``target_date`` resolves the current period/sub-period pointers.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                FirdariaFactory.from_subject,
                subj,
                target_date=target_date,
                life_cap_years=life_cap_years,
            )

            return {"status": "OK", "firdaria": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_firdaria failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 21d. Horary Indicators
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_horary_indicators(
        subject: MCPSubjectInput,
        is_moon_void: Optional[bool] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Assemble horary significators and the considerations before judgment.

        Querent (1st house) and quesited (7th house) significators via
        classical rulership, the Ascendant degree from the true Ascendant
        point (Whole Sign safe), the considerations as stable keys, and the
        chart's mutual receptions. Pass ``is_moon_void`` from the
        void-of-course tool when known; omitted, the Moon considerations are
        simply not evaluated.
        """
        try:
            subj = await run_heavy(_build_subject_from_model, subject)
            result = await run_heavy(
                HoraryIndicatorsFactory.from_subject,
                subj,
                is_moon_void=is_moon_void,
            )

            return {"status": "OK", "horary_indicators": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_horary_indicators failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 22. Dominants
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_dominants(
        subject: MCPSubjectInput,
        strategy: Literal["modern", "almuten_figuris", "elemental"] = "modern",
        active_points: Optional[list[str]] = None,
        distribution_method: Literal["weighted", "pure_count"] = "weighted",
        custom_distribution_weights: Optional[dict[str, float]] = None,
        include_accidental_dignities: bool = False,
        include_score_breakdown: bool = False,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Compute a chart's dominants (planet, sign, element, modality, house).

        ``strategy`` selects the calculation school: 'modern' (Astrotheme-style
        weighted), 'almuten_figuris' (traditional Lord of the Geniture), or
        'elemental' (element/modality balance). The modern method also reports
        polarity, hemispheres and quadrants.
        """
        try:
            if active_points:
                # Same alias/case canonicalization the REST models apply — raw
                # names like 'asc' would be silently dropped by the factories.
                active_points = _resolve_active_points(active_points)
            subj = await run_heavy(_build_subject_from_model, subject, active_points=active_points)
            result = await run_heavy(
                DominantsFactory.from_subject,
                subj,
                strategy=strategy,
                active_points=active_points,
                distribution_method=distribution_method,
                custom_weights=custom_distribution_weights,
                include_accidental_dignities=include_accidental_dignities,
                include_score_breakdown=include_score_breakdown,
            )

            return {"status": "OK", "dominants": dump(result, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_dominants failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 23. Void-of-Course Moon
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_void_of_course_moon(
        year: int,
        month: int,
        day: int,
        hour: int,
        timezone: str,
        minute: int = 0,
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Void-of-course Moon for a moment.

        The Moon is void of course once it has perfected its last exact Ptolemaic
        aspect to a traditional planet while in its current sign, and stays void
        until it ingresses the next sign. Geocentric, so no location is required;
        ``timezone`` interprets the clock time and localises the returned window.

        Returns ``moon_voc`` with is_void, moon_sign, next_sign, ingress /
        ingress_local, void_start / void_start_local, void_end / void_end_local,
        and last_aspect / next_aspect (each with planet, aspect, degrees, time,
        time_local) — the same shape as the REST ``/api/v6/moon/void-of-course`` endpoint.
        """
        try:
            # Mirror the REST MoonVocRequestModel validation: a sidereal_mode
            # under Tropical is a silent no-op in kerykeion, so reject the
            # inconsistent combination (and the missing-mode case) up front.
            if sidereal_mode is not None and zodiac_type != "Sidereal":
                return {"status": "ERROR", "message": "Set zodiac_type='Sidereal' when sidereal_mode is provided."}
            if zodiac_type == "Sidereal" and sidereal_mode is None:
                return {"status": "ERROR", "message": "sidereal_mode is required when zodiac_type='Sidereal'."}
            model = await run_heavy(
                VoidOfCourseMoonFactory.from_datetime,
                year,
                month,
                day,
                hour,
                minute,
                tz_str=timezone,
                zodiac_type=zodiac_type,
                sidereal_mode=sidereal_mode,
            )

            # Same reshaping as the REST /api/v6/moon/void-of-course handler.
            payload = _moon_voc_payload(model, ZoneInfo(timezone))
            return _strip_nulls(payload) if omit_nulls else payload

        except Exception as exc:
            logger.error("get_void_of_course_moon failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 24. Sun Times
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_sun_times(
        year: int,
        month: int,
        day: int,
        latitude: float,
        longitude: float,
        timezone: str,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Sunrise, sunset, solar noon and day length for a civil date at a location.

        Also reports civil / nautical / astronomical twilight. A value is null when
        the event does not occur (e.g. rise/set on polar day/night). Times are UTC
        ISO-8601 with ``_local`` companions (HH:MM for rise/set/noon, full ISO for
        twilight); ``day_length`` is "H:MM" — the same shape as the REST
        ``/api/v6/sun/times`` endpoint.
        """
        try:
            model = await run_heavy(
                SunTimesFactory.from_date,
                year,
                month,
                day,
                latitude=latitude,
                longitude=longitude,
                tz_str=timezone,
            )

            # Same reshaping as the REST /api/v6/sun/times handler.
            payload = _sun_times_payload(model)
            return _strip_nulls(payload) if omit_nulls else payload

        except Exception as exc:
            logger.error("get_sun_times failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 25. Planetary Hours
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_planetary_hours(
        year: int,
        month: int,
        day: int,
        hour: int,
        latitude: float,
        longitude: float,
        timezone: str,
        minute: int = 0,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """The 24 Chaldean planetary hours for the planetary day containing a moment.

        Day and night are each divided into twelve unequal hours
        (sunrise->sunset, sunset->next sunrise); the first hour is ruled by the
        weekday's planet, then the Chaldean order cycles.

        Returns ``planetary_hours`` with day_ruler, current_index, current_ruler,
        current_is_day, sunrise/sunset/next_sunrise (UTC ISO-8601) and the 24
        ``hours`` (index, ruler, is_day, start, end) — the same shape as the REST
        ``/api/v6/sun/planetary-hours`` endpoint.
        """
        try:
            model = await run_heavy(
                PlanetaryHoursFactory.from_datetime,
                year,
                month,
                day,
                hour,
                minute,
                latitude=latitude,
                longitude=longitude,
                tz_str=timezone,
            )

            # Same reshaping as the REST /api/v6/sun/planetary-hours handler.
            payload = _planetary_hours_payload(model)
            return _strip_nulls(payload) if omit_nulls else payload

        except Exception as exc:
            logger.error("get_planetary_hours failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 26. Lunations
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_lunations(
        start_date: str,
        end_date: str,
        phases: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Find lunations (New / First Quarter / Full / Last Quarter) in a date range.

        Returns events ordered chronologically, each with the Sun and Moon zodiac
        positions at the exact phase. Dates are ISO (treated as UTC); the span is
        capped at ~10 years. ``phases`` optionally narrows to a subset of
        'new', 'first_quarter', 'full', 'last_quarter'.
        """
        try:
            err = _validate_iso_range(start_date, end_date)
            if err is not None:
                return err
            if phases is not None:
                allowed = {"new", "first_quarter", "full", "last_quarter"}
                invalid = [p for p in phases if p not in allowed]
                if invalid:
                    return {"status": "ERROR", "message": f"Invalid phase(s): {invalid}. Allowed: {sorted(allowed)}"}

            result = await run_heavy(
                LunationFinderFactory.from_iso_range,
                start_date=start_date,
                end_date=end_date,
                phases=phases,
            )

            return {"status": "OK", "lunations": dump(result.lunations, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_lunations failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 27. Retrograde Stations
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_retrograde_stations(
        start_date: str,
        end_date: str,
        planets: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Find planetary retrograde/direct stations (motion reversals) in a range.

        Returns stations ordered chronologically (SR = retrograde, SD = direct),
        each with the zodiac position at the station. Dates are ISO (treated as
        UTC), span capped at ~10 years. ``planets`` optionally narrows to a subset
        of Mercury..Pluto (the Sun and Moon never station).
        """
        try:
            err = _validate_iso_range(start_date, end_date)
            if err is not None:
                return err
            if planets is not None:
                allowed = {"Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
                invalid = [p for p in planets if p not in allowed]
                if invalid:
                    return {"status": "ERROR", "message": f"Invalid or non-stationing planet(s): {invalid}. Allowed: {sorted(allowed)}"}
                planets = list(dict.fromkeys(planets))

            result = await run_heavy(
                RetrogradeStationFactory.from_iso_range,
                start_date=start_date,
                end_date=end_date,
                planets=planets,
            )

            return {"status": "OK", "stations": dump(result.stations, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_retrograde_stations failed | exception=%s", type(exc).__name__)
            raise

    # -----------------------------------------------------------------------
    # 28. Sign Ingresses
    # -----------------------------------------------------------------------

    @mcp.tool()
    async def get_sign_ingresses(
        start_date: str,
        end_date: str,
        planets: Optional[list[str]] = None,
        omit_nulls: bool = True,
    ) -> dict[str, Any]:
        """Find zodiac sign ingresses (30 degree boundary crossings) in a range.

        Returns ingresses ordered chronologically with from/to signs; retrograde
        re-entries are included. Dates are ISO (treated as UTC), span capped at
        ~10 years. ``planets`` optionally narrows the set (defaults to Sun..Pluto;
        the Moon is opt-in).
        """
        try:
            err = _validate_iso_range(start_date, end_date)
            if err is not None:
                return err
            if planets is not None:
                allowed = {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Moon"}
                invalid = [p for p in planets if p not in allowed]
                if invalid:
                    return {"status": "ERROR", "message": f"Invalid planet(s): {invalid}. Allowed: {sorted(allowed)}"}
                planets = list(dict.fromkeys(planets))

            result = await run_heavy(
                SignIngressFactory.from_iso_range,
                start_date=start_date,
                end_date=end_date,
                planets=planets,
            )

            return {"status": "OK", "ingresses": dump(result.ingresses, omit_nulls=omit_nulls)}

        except Exception as exc:
            logger.error("get_sign_ingresses failed | exception=%s", type(exc).__name__)
            raise
