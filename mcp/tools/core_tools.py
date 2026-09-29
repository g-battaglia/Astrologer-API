"""Core MCP tools for the Astrologer API v6.

Nine tools ported from the v5 bozza, updated for kerykeion v6.
Each tool is registered on a FastMCP instance via ``register_core_tools(mcp)``.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Literal, Optional, Sequence

from pydantic import Field

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    to_context,
)
from kerykeion import PlanetaryReturnFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

from ...types.request_models import DEFAULT_NAKSHATRA_AYANAMSA
from ...utils.clock import utc_now
from ...utils.router_utils import (
    add_nakshatra_ayanamsa_kwarg,
    chart_data_payload,
    chart_payload,
    context_payload,
    dump,
    guard_return_factory_v6_kwargs,
    normalize_coordinate,
    resolve_nation,
    run_heavy,
    subject_context_payload,
)
from ..types import MCPSubjectInput, MCPReturnLocationInput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

# Common field name mistakes → correct MCP parameter name
_FIELD_CORRECTIONS: dict[str, str] = {
    "lat": "latitude",
    "lng": "longitude",
    "lon": "longitude",
    "long": "longitude",
    "tz": "timezone",
    "tz_str": "timezone",
    "country": "nation",
    "house_system": "houses_system_identifier",
    "houses": "houses_system_identifier",
    "zodiac": "zodiac_type",
    "sidereal": "sidereal_mode",
    "perspective": "perspective_type",
}

# Kerykeion internal names → MCP-facing names (for error message translation)
_KERYKEION_TO_MCP: dict[str, str] = {
    "lat": "latitude",
    "lng": "longitude",
    "tz_str": "timezone",
}


def _resolve_active_points(points: Optional[Sequence[str]] = None) -> list[str]:
    if points:
        # Same alias/case normalization the REST models apply via their
        # validators ('asc' -> 'Ascendant', 'north_node' -> ...): the
        # subject-model resource documents point names as case-insensitive
        # and alias-aware "in all API requests", and kerykeion silently
        # drops names it does not recognize.
        from ...types.request_models import _normalize_active_points

        return _normalize_active_points(list(points)) or []
    return list(DEFAULT_ACTIVE_POINTS)


def _resolve_active_aspects(aspects: Optional[list[dict]] = None) -> Optional[list[dict]]:
    """Resolve active aspects from a tool argument.

    Returns ``None`` when the caller omits aspects so kerykeion's
    ``ChartDataFactory`` applies its per-chart-type default — the natal orbs
    (``DEFAULT_ACTIVE_ASPECTS``, up to 6°) for natal/synastry/composite charts,
    and the tighter ``PREDICTIVE_ACTIVE_ASPECTS`` (3°) for transit/return/
    progression charts. Mirrors the REST ``resolve_active_aspects`` helper:
    returning a fixed natal default here would force natal-wide orbs onto
    predictive charts (audit M7).
    """
    if aspects:
        for i, asp in enumerate(aspects):
            if "name" not in asp or "orb" not in asp:
                raise ValueError(f'active_aspects[{i}] must have \'name\' and \'orb\' keys, e.g. {{"name": "conjunction", "orb": 10}}. Got: {asp}')
        return aspects
    return None


def _chart_data_kwargs(
    *,
    active_points,
    active_aspects,
    axis_orb_limit=None,
    point_orb_adjustments=None,
    point_orb_adjustment_strategy="max_explicit",
    distribution_method=None,
    custom_distribution_weights=None,
) -> dict[str, Any]:
    """Build the shared keyword block for ``ChartDataFactory.create_chart_data``.

    The 7 MCP chart tools route through ``create_chart_data`` (not the
    convenience ``create_*_chart_data`` methods): when this was introduced
    (kerykeion 6.0.0a60, audit L-group) only the former accepted
    ``axis_orb_limit`` / ``point_orb_adjustments`` /
    ``point_orb_adjustment_strategy``; the uniform routing is kept even though
    newer kerykeion releases accept them on the convenience methods too.
    """
    return {
        "active_points": active_points,
        "active_aspects": active_aspects,
        "axis_orb_limit": axis_orb_limit,
        "point_orb_adjustments": point_orb_adjustments,
        "point_orb_adjustment_strategy": point_orb_adjustment_strategy,
        "distribution_method": distribution_method or "weighted",
        "custom_distribution_weights": custom_distribution_weights,
    }


def _extract_v6_config(args: dict[str, Any]) -> dict[str, Any]:
    """Extract v6 calculation config kwargs from tool arguments."""
    kwargs: dict[str, Any] = {}
    if args.get("calculate_dignities"):
        kwargs["calculate_dignities"] = True
    if args.get("calculate_nakshatra"):
        kwargs["calculate_nakshatra"] = True
    if args.get("calculate_gauquelin"):
        kwargs["calculate_gauquelin"] = True
    if args.get("calculate_nutation"):
        kwargs["calculate_nutation"] = True
    if args.get("calculate_local_space"):
        kwargs["calculate_local_space"] = True
    if args.get("active_fixed_stars"):
        kwargs["active_fixed_stars"] = args["active_fixed_stars"]
    # Same "only when it differs from the default" rule the REST side applies
    # (add_nakshatra_ayanamsa_kwarg): `None` is a real choice — the uncorrected
    # legacy reading — so the test is a comparison with the default, not
    # truthiness, and the key is absent when the caller never named it.
    if "nakshatra_ayanamsa" in args and args["nakshatra_ayanamsa"] != DEFAULT_NAKSHATRA_AYANAMSA:
        kwargs["nakshatra_ayanamsa"] = args["nakshatra_ayanamsa"]
    return kwargs


def _translate_error_message(message: str) -> str:
    """Translate kerykeion internal field names to MCP-facing names in error messages."""
    for internal, public in _KERYKEION_TO_MCP.items():
        message = message.replace(f"'{internal}'", f"'{public}'")
        message = message.replace(f"`{internal}`", f"`{public}`")
        message = message.replace(f" {internal} ", f" {public} ")
        message = message.replace(f" {internal},", f" {public},")
        message = message.replace(f" {internal}.", f" {public}.")
    return message


def _build_subject(
    name,
    year,
    month,
    day,
    hour,
    minute,
    city,
    nation,
    second=0,
    timezone=None,
    longitude=None,
    latitude=None,
    zodiac_type="Tropical",
    houses_system_identifier="P",
    perspective_type="Apparent Geocentric",
    sidereal_mode=None,
    geonames_username=None,
    active_points=None,
    altitude=None,
    is_dst=None,
    custom_ayanamsa_t0=None,
    custom_ayanamsa_ayan_t0=None,
    # v6 calc flags
    calculate_dignities=False,
    calculate_nakshatra=False,
    calculate_gauquelin=False,
    calculate_nutation=False,
    calculate_local_space=False,
    nakshatra_ayanamsa=DEFAULT_NAKSHATRA_AYANAMSA,
    active_fixed_stars=None,
    active_midpoints=None,
    **_extra,  # Absorb unexpected keys from dict unpacking
):
    # Check for common field name mistakes in extra keys
    if _extra:
        corrections = []
        for key in _extra:
            if key in _FIELD_CORRECTIONS:
                corrections.append(f"'{key}' → use '{_FIELD_CORRECTIONS[key]}'")
        if corrections:
            raise ValueError(f"Unknown field(s): {', '.join(corrections)}. See astrologer://docs/subject-model for the full field reference.")
        logger.debug("_build_subject ignored %d unexpected field(s)", len(_extra))

    resolved_points = _resolve_active_points(active_points)
    online = bool(geonames_username)

    v6_kwargs: dict[str, Any] = {}
    if calculate_dignities:
        v6_kwargs["calculate_dignities"] = True
    if calculate_nakshatra:
        v6_kwargs["calculate_nakshatra"] = True
    if calculate_gauquelin:
        v6_kwargs["calculate_gauquelin"] = True
    if calculate_nutation:
        v6_kwargs["calculate_nutation"] = True
    if calculate_local_space:
        v6_kwargs["calculate_local_space"] = True
    if active_fixed_stars:
        v6_kwargs["active_fixed_stars"] = active_fixed_stars
    if nakshatra_ayanamsa != DEFAULT_NAKSHATRA_AYANAMSA:
        v6_kwargs["nakshatra_ayanamsa"] = nakshatra_ayanamsa

    try:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            seconds=second,
            city=city,
            nation=resolve_nation(nation) or "GB",
            lng=longitude,
            lat=latitude,
            tz_str=timezone,
            geonames_username=geonames_username,
            online=online,
            zodiac_type=zodiac_type or "Tropical",
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier or "P",
            perspective_type=perspective_type or "Apparent Geocentric",
            is_dst=is_dst,
            altitude=altitude,
            active_points=resolved_points,
            suppress_geonames_warning=True,
            custom_ayanamsa_t0=custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
            **v6_kwargs,
        )
    except Exception as exc:
        translated = _translate_error_message(str(exc))
        # Not every exception type reconstructs from a single message string
        # (e.g. pydantic ValidationError) — fall back to ValueError rather
        # than masking the original error with a TypeError.
        try:
            new_exc: Exception = type(exc)(translated)
        except Exception:
            new_exc = ValueError(translated)
        raise new_exc from exc

    _apply_active_midpoints(subject, active_midpoints)
    return subject


def _apply_active_midpoints(subject, active_midpoints) -> None:
    """Post-populate a subject with synthetic midpoint points so the chart
    drawer can render them on the wheel — mirrors the REST ``build_subject``.
    """
    if active_midpoints:
        from kerykeion import MidpointFactory  # local import keeps cold path light

        subject.active_midpoints = MidpointFactory.compute_active_midpoint_points(subject, active_midpoints)


def _build_subject_from_model(m: MCPSubjectInput, active_points=None):
    """Build an AstrologicalSubject from a validated MCPSubjectInput model."""
    resolved_points = _resolve_active_points(active_points)
    online = bool(m.geonames_username)

    v6_kwargs: dict[str, Any] = {}
    if m.calculate_dignities:
        v6_kwargs["calculate_dignities"] = True
    if m.calculate_nakshatra:
        v6_kwargs["calculate_nakshatra"] = True
    if m.calculate_gauquelin:
        v6_kwargs["calculate_gauquelin"] = True
    if m.calculate_nutation:
        v6_kwargs["calculate_nutation"] = True
    if m.calculate_local_space:
        v6_kwargs["calculate_local_space"] = True
    if m.active_fixed_stars:
        v6_kwargs["active_fixed_stars"] = m.active_fixed_stars
    add_nakshatra_ayanamsa_kwarg(v6_kwargs, m)

    try:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=m.name,
            year=m.year,
            month=m.month,
            day=m.day,
            hour=m.hour,
            minute=m.minute,
            seconds=m.second,
            city=m.city,
            nation=resolve_nation(m.nation) or "GB",
            lng=m.longitude,
            lat=m.latitude,
            tz_str=m.timezone,
            geonames_username=m.geonames_username,
            online=online,
            zodiac_type=m.zodiac_type or "Tropical",
            sidereal_mode=m.sidereal_mode,
            houses_system_identifier=m.houses_system_identifier or "P",
            perspective_type=m.perspective_type or "Apparent Geocentric",
            is_dst=m.is_dst,
            altitude=m.altitude,
            active_points=resolved_points,
            suppress_geonames_warning=True,
            custom_ayanamsa_t0=m.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=m.custom_ayanamsa_ayan_t0,
            **v6_kwargs,
        )
    except Exception as exc:
        translated = _translate_error_message(str(exc))
        # Not every exception type reconstructs from a single message string
        # (e.g. pydantic ValidationError) — fall back to ValueError rather
        # than masking the original error with a TypeError.
        try:
            new_exc: Exception = type(exc)(translated)
        except Exception:
            new_exc = ValueError(translated)
        raise new_exc from exc

    _apply_active_midpoints(subject, getattr(m, "active_midpoints", None))
    return subject


def _build_transit_subject_from_model(reference_subject, m: MCPSubjectInput, active_points=None, natal_model: Optional[MCPSubjectInput] = None):
    """Build transit subject from MCPSubjectInput, inheriting zodiac/house settings from natal.

    The USER-sidereal custom ayanamsa pair and the v6 calc flags are inherited
    from the natal request model (``natal_model``) — mirroring the REST
    ``build_transit_subject`` helper. Without the ayanamsa pair a sidereal
    'USER' transit ring would raise (kerykeion requires it for that mode).
    """
    resolved_points = _resolve_active_points(active_points)
    online = bool(m.geonames_username)

    return AstrologicalSubjectFactory.from_birth_data(
        name=m.name or "Transit",
        year=m.year,
        month=m.month,
        day=m.day,
        hour=m.hour,
        minute=m.minute,
        seconds=m.second,
        city=m.city,
        nation=resolve_nation(m.nation) or reference_subject.nation,
        lng=m.longitude,
        lat=m.latitude,
        tz_str=m.timezone,
        geonames_username=m.geonames_username,
        online=online,
        zodiac_type=reference_subject.zodiac_type,
        sidereal_mode=reference_subject.sidereal_mode,
        houses_system_identifier=reference_subject.houses_system_identifier,
        perspective_type=reference_subject.perspective_type,
        is_dst=m.is_dst,
        altitude=m.altitude,
        active_points=resolved_points,
        suppress_geonames_warning=True,
        custom_ayanamsa_t0=natal_model.custom_ayanamsa_t0 if natal_model else None,
        custom_ayanamsa_ayan_t0=natal_model.custom_ayanamsa_ayan_t0 if natal_model else None,
        **_v6_kwargs_from_model(natal_model),
    )


def _v6_kwargs_from_model(m: Optional[MCPSubjectInput]) -> dict[str, Any]:
    """Extract the v6 calculation flags from an MCPSubjectInput as factory kwargs."""
    kwargs: dict[str, Any] = {}
    if m is None:
        return kwargs
    if m.calculate_dignities:
        kwargs["calculate_dignities"] = True
    if m.calculate_nakshatra:
        kwargs["calculate_nakshatra"] = True
    if m.calculate_gauquelin:
        kwargs["calculate_gauquelin"] = True
    if m.calculate_nutation:
        kwargs["calculate_nutation"] = True
    if m.calculate_local_space:
        kwargs["calculate_local_space"] = True
    if m.active_fixed_stars:
        kwargs["active_fixed_stars"] = m.active_fixed_stars
    add_nakshatra_ayanamsa_kwarg(kwargs, m)
    return kwargs


def _build_return_factory_from_model(
    natal_subject,
    location: Optional[MCPReturnLocationInput] = None,
    subject_input: Optional[MCPSubjectInput] = None,
):
    """Build PlanetaryReturnFactory from natal subject and optional MCPReturnLocationInput.

    ``subject_input`` propagates the natal v6 calculation flags (fixed stars,
    dignities, …) so the return subject computes the same enrichments.
    """
    v6_kwargs = _v6_kwargs_from_model(subject_input)
    # REST parity (build_return_factory): refuse a nakshatra_ayanamsa the
    # installed engine's return factory cannot honor, rather than dropping it
    # and answering with mansions read off uncorrected longitudes.
    guard_return_factory_v6_kwargs(v6_kwargs)
    # USER-sidereal natal subjects need the custom ayanamsa pair on the
    # factory too, or building the return subject raises (REST parity:
    # build_return_factory's custom_ayanamsa_kwargs).
    if subject_input is not None:
        if subject_input.custom_ayanamsa_t0 is not None:
            v6_kwargs["custom_ayanamsa_t0"] = subject_input.custom_ayanamsa_t0
        if subject_input.custom_ayanamsa_ayan_t0 is not None:
            v6_kwargs["custom_ayanamsa_ayan_t0"] = subject_input.custom_ayanamsa_ayan_t0
    if location is not None:
        nation = resolve_nation(location.nation) or natal_subject.nation
        if location.latitude is not None and location.longitude is not None and location.timezone is not None:
            return PlanetaryReturnFactory(
                natal_subject,
                city=location.city or natal_subject.city,
                nation=nation,
                lng=normalize_coordinate(location.longitude),
                lat=normalize_coordinate(location.latitude),
                tz_str=location.timezone,
                online=False,
                altitude=location.altitude,
                **v6_kwargs,
            )
        else:
            return PlanetaryReturnFactory(
                natal_subject,
                city=location.city or natal_subject.city,
                nation=nation,
                online=True,
                geonames_username=location.geonames_username,
                altitude=location.altitude,
                **v6_kwargs,
            )
    return PlanetaryReturnFactory(
        natal_subject,
        city=natal_subject.city,
        nation=natal_subject.nation,
        lng=normalize_coordinate(natal_subject.lng),
        lat=normalize_coordinate(natal_subject.lat),
        tz_str=natal_subject.tz_str,
        online=False,
        altitude=getattr(natal_subject, "altitude", None),
        **v6_kwargs,
    )


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_core_tools(mcp):
    """Register the nine core MCP tools on the given FastMCP instance."""

    # ------------------------------------------------------------------ 1
    @mcp.tool()
    async def get_current_moment(
        # Subject configuration
        name: str = "Now",
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        houses_system_identifier: str = "P",
        perspective_type: str = "Apparent Geocentric",
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
        # v6 calc flags
        calculate_dignities: bool = False,
        calculate_nakshatra: bool = False,
        calculate_gauquelin: bool = False,
        calculate_nutation: bool = False,
        calculate_local_space: bool = False,
        nakshatra_ayanamsa: Optional[str] = DEFAULT_NAKSHATRA_AYANAMSA,
        active_fixed_stars: Optional[list[str]] = None,
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Return planetary positions for the current moment (UTC, Greenwich).

        Useful for getting a snapshot of the sky right now. Supports tropical
        and sidereal zodiacs, multiple house systems, and all v6 calculation
        flags (dignities, nakshatra, Gauquelin sectors, nutation, local space).

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        try:
            now_utc = utc_now()

            v6_kwargs = _extract_v6_config(
                {
                    "calculate_dignities": calculate_dignities,
                    "calculate_nakshatra": calculate_nakshatra,
                    "calculate_gauquelin": calculate_gauquelin,
                    "calculate_nutation": calculate_nutation,
                    "calculate_local_space": calculate_local_space,
                    "nakshatra_ayanamsa": nakshatra_ayanamsa,
                    "active_fixed_stars": active_fixed_stars,
                }
            )

            resolved_points = _resolve_active_points(active_points)

            subject = await run_heavy(
                AstrologicalSubjectFactory.from_birth_data,
                name=name,
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
                zodiac_type=zodiac_type or "Tropical",
                sidereal_mode=sidereal_mode,
                houses_system_identifier=houses_system_identifier or "P",
                perspective_type=perspective_type or "Apparent Geocentric",
                active_points=resolved_points,
                suppress_geonames_warning=True,
                custom_ayanamsa_t0=custom_ayanamsa_t0,
                custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
                **v6_kwargs,
            )

            if include_svg:
                resolved_aspects = _resolve_active_aspects(active_aspects)
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "Natal",
                    subject,
                    **_chart_data_kwargs(
                        active_points=resolved_points,
                        active_aspects=resolved_aspects,
                        axis_orb_limit=axis_orb_limit,
                        point_orb_adjustments=point_orb_adjustments,
                        point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                        distribution_method=distribution_method,
                        custom_distribution_weights=custom_distribution_weights,
                    ),
                )
                return await run_heavy(
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )

            if include_ai_context:
                return await run_heavy(subject_context_payload, subject, omit_nulls=omit_nulls)

            return {"status": "OK", "subject": dump(subject, omit_nulls=omit_nulls)}
        except Exception as exc:
            logger.error("get_current_moment failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 2
    @mcp.tool()
    async def get_subject(
        # Subject params
        name: str = "Subject",
        year: int = 2000,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        city: str = "Greenwich",
        nation: str = "GB",
        timezone: Optional[str] = None,
        longitude: Optional[float] = None,
        latitude: Optional[float] = None,
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        houses_system_identifier: str = "P",
        perspective_type: str = "Apparent Geocentric",
        geonames_username: Optional[str] = None,
        altitude: Optional[float] = None,
        is_dst: Optional[bool] = None,
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
        # v6 calc flags
        calculate_dignities: bool = False,
        calculate_nakshatra: bool = False,
        calculate_gauquelin: bool = False,
        calculate_nutation: bool = False,
        calculate_local_space: bool = False,
        nakshatra_ayanamsa: Optional[str] = DEFAULT_NAKSHATRA_AYANAMSA,
        active_fixed_stars: Optional[list[str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        # Output
        include_ai_context: bool = True,
        omit_nulls: bool = True,
    ) -> dict:
        """Build an astrological subject from birth data and return its model.

        The subject contains all calculated planetary positions, house cusps,
        and metadata. When include_ai_context is True (default), an
        AI-optimized textual description is included alongside the raw data.
        ``active_points`` optionally restricts the computed points (REST
        ``/api/v6/subject`` parity).
        """
        try:
            resolved_points = _resolve_active_points(active_points)

            subject = await run_heavy(
                _build_subject,
                name=name,
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                city=city,
                nation=nation,
                second=second,
                timezone=timezone,
                longitude=longitude,
                latitude=latitude,
                zodiac_type=zodiac_type,
                sidereal_mode=sidereal_mode,
                houses_system_identifier=houses_system_identifier,
                perspective_type=perspective_type,
                geonames_username=geonames_username,
                altitude=altitude,
                is_dst=is_dst,
                custom_ayanamsa_t0=custom_ayanamsa_t0,
                custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
                calculate_dignities=calculate_dignities,
                calculate_nakshatra=calculate_nakshatra,
                calculate_gauquelin=calculate_gauquelin,
                calculate_nutation=calculate_nutation,
                calculate_local_space=calculate_local_space,
                nakshatra_ayanamsa=nakshatra_ayanamsa,
                active_fixed_stars=active_fixed_stars,
                active_points=resolved_points,
            )

            if include_ai_context:
                return await run_heavy(subject_context_payload, subject, omit_nulls=omit_nulls)

            return {"status": "OK", "subject": dump(subject, omit_nulls=omit_nulls)}
        except Exception as exc:
            logger.error("get_subject failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 3
    @mcp.tool()
    async def get_birth_chart(
        # Subject params
        name: str = "Subject",
        year: int = 2000,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        city: str = "Greenwich",
        nation: str = "GB",
        timezone: Optional[str] = None,
        longitude: Optional[float] = None,
        latitude: Optional[float] = None,
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        houses_system_identifier: str = "P",
        perspective_type: str = "Apparent Geocentric",
        geonames_username: Optional[str] = None,
        altitude: Optional[float] = None,
        is_dst: Optional[bool] = None,
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
        # v6 calc flags
        calculate_dignities: bool = False,
        calculate_nakshatra: bool = False,
        calculate_gauquelin: bool = False,
        calculate_nutation: bool = False,
        calculate_local_space: bool = False,
        nakshatra_ayanamsa: Optional[str] = DEFAULT_NAKSHATRA_AYANAMSA,
        active_fixed_stars: Optional[list[str]] = None,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate a natal (birth) chart for a single subject.

        Returns chart data with planetary positions, house cusps, aspects,
        and element/quality distributions. Optionally renders an SVG chart
        image or includes an AI-optimized context summary.

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        try:
            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            subject = await run_heavy(
                _build_subject,
                name=name,
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                city=city,
                nation=nation,
                second=second,
                timezone=timezone,
                longitude=longitude,
                latitude=latitude,
                zodiac_type=zodiac_type,
                sidereal_mode=sidereal_mode,
                houses_system_identifier=houses_system_identifier,
                perspective_type=perspective_type,
                geonames_username=geonames_username,
                active_points=resolved_points,
                altitude=altitude,
                is_dst=is_dst,
                custom_ayanamsa_t0=custom_ayanamsa_t0,
                custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
                calculate_dignities=calculate_dignities,
                calculate_nakshatra=calculate_nakshatra,
                calculate_gauquelin=calculate_gauquelin,
                calculate_nutation=calculate_nutation,
                calculate_local_space=calculate_local_space,
                nakshatra_ayanamsa=nakshatra_ayanamsa,
                active_fixed_stars=active_fixed_stars,
            )

            chart_data = await run_heavy(
                ChartDataFactory.create_chart_data,
                "Natal",
                subject,
                **_chart_data_kwargs(
                    active_points=resolved_points,
                    active_aspects=resolved_aspects,
                    axis_orb_limit=axis_orb_limit,
                    point_orb_adjustments=point_orb_adjustments,
                    point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                    distribution_method=distribution_method,
                    custom_distribution_weights=custom_distribution_weights,
                ),
            )

            if include_svg:
                return await run_heavy(
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )

            if include_ai_context:
                return await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)

            return await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)
        except Exception as exc:
            logger.error("get_birth_chart failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 4
    @mcp.tool()
    async def get_synastry(
        first_subject: MCPSubjectInput,
        second_subject: MCPSubjectInput,
        # Synastry options
        include_house_comparison: bool = True,
        include_relationship_score: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate synastry (bi-wheel) chart data between two subjects.

        Compares planetary positions and house placements of two charts.
        Includes inter-chart aspects, house comparison, and an optional
        relationship compatibility score (Ciro Discepolo method).

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        try:
            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            subj1 = await run_heavy(_build_subject_from_model, first_subject, active_points=resolved_points)
            subj2 = await run_heavy(_build_subject_from_model, second_subject, active_points=resolved_points)

            chart_data = await run_heavy(
                ChartDataFactory.create_chart_data,
                "Synastry",
                subj1,
                subj2,
                include_house_comparison=include_house_comparison,
                include_relationship_score=include_relationship_score,
                **_chart_data_kwargs(
                    active_points=resolved_points,
                    active_aspects=resolved_aspects,
                    axis_orb_limit=axis_orb_limit,
                    point_orb_adjustments=point_orb_adjustments,
                    point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                    distribution_method=distribution_method,
                    custom_distribution_weights=custom_distribution_weights,
                ),
            )

            if include_svg:
                return await run_heavy(
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )

            if include_ai_context:
                return await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)

            return await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)
        except Exception as exc:
            logger.error("get_synastry failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 5
    @mcp.tool()
    async def get_transit(
        first_subject: MCPSubjectInput,
        transit_subject: MCPSubjectInput,
        # Transit options
        include_house_comparison: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate transit chart data overlaying transiting planets on a natal chart.

        The first_subject is the natal (birth) chart. The transit_subject
        represents the transiting moment and inherits zodiac/house settings
        from the natal chart. Returns inter-chart aspects showing which
        transiting planets aspect natal positions.

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        try:
            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            natal = await run_heavy(_build_subject_from_model, first_subject, active_points=resolved_points)
            transit = await run_heavy(
                _build_transit_subject_from_model,
                natal,
                transit_subject,
                active_points=resolved_points,
                natal_model=first_subject,
            )

            chart_data = await run_heavy(
                ChartDataFactory.create_chart_data,
                "Transit",
                natal,
                transit,
                include_house_comparison=include_house_comparison,
                **_chart_data_kwargs(
                    active_points=resolved_points,
                    active_aspects=resolved_aspects,
                    axis_orb_limit=axis_orb_limit,
                    point_orb_adjustments=point_orb_adjustments,
                    point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                    distribution_method=distribution_method,
                    custom_distribution_weights=custom_distribution_weights,
                ),
            )

            if include_svg:
                return await run_heavy(
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )

            if include_ai_context:
                return await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)

            return await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)
        except Exception as exc:
            logger.error("get_transit failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 6
    @mcp.tool()
    async def get_composite(
        first_subject: MCPSubjectInput,
        second_subject: MCPSubjectInput,
        # Composite options
        composite_type: Literal["Midpoint", "Davison"] = "Midpoint",
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate a composite chart merging two subjects into one chart.

        Supports two composite methods:
        - "Midpoint" (default): midpoints of each pair of planets.
        - "Davison": time/space midpoint creating a real moment in time.

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        try:
            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            subj1 = await run_heavy(_build_subject_from_model, first_subject, active_points=resolved_points)
            subj2 = await run_heavy(_build_subject_from_model, second_subject, active_points=resolved_points)

            composite_factory = CompositeSubjectFactory(subj1, subj2)

            if composite_type == "Davison":
                # Davison rebuilds a real subject at the time/space midpoint, so it
                # needs the USER-sidereal custom ayanamsa pair (from first_subject);
                # without it kerykeion raises for sidereal_mode='USER'. Mirror REST
                # create_composite_chart_data.
                composite_subject = await run_heavy(
                    composite_factory.get_davison_composite_subject_model,
                    custom_ayanamsa_t0=first_subject.custom_ayanamsa_t0,
                    custom_ayanamsa_ayan_t0=first_subject.custom_ayanamsa_ayan_t0,
                )
            else:
                composite_subject = await run_heavy(composite_factory.get_midpoint_composite_subject_model)

            chart_data = await run_heavy(
                ChartDataFactory.create_chart_data,
                "Composite",
                composite_subject,
                **_chart_data_kwargs(
                    active_points=resolved_points,
                    active_aspects=resolved_aspects,
                    axis_orb_limit=axis_orb_limit,
                    point_orb_adjustments=point_orb_adjustments,
                    point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                    distribution_method=distribution_method,
                    custom_distribution_weights=custom_distribution_weights,
                ),
            )

            if include_svg:
                return await run_heavy(
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )

            if include_ai_context:
                return await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)

            return await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)
        except Exception as exc:
            logger.error("get_composite failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 7
    @mcp.tool()
    async def get_solar_return(
        subject: MCPSubjectInput,
        year: Optional[int] = None,
        month: Annotated[Optional[int], Field(ge=1, le=12)] = None,
        day: Annotated[Optional[int], Field(ge=1, le=31)] = None,
        iso_datetime: Optional[str] = None,
        direction: Literal["next", "previous"] = "next",
        # Return options
        wheel_type: Literal["dual", "single"] = "dual",
        return_location: Optional[MCPReturnLocationInput] = None,
        include_house_comparison: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate a solar return chart for a given year.

        A solar return occurs when the transiting Sun returns to its exact
        natal longitude. You can search by year (finds the return after
        Jan 1), by year+month+day (finds the next return after that date),
        or by iso_datetime (finds the next return after that moment).

        wheel_type "dual" shows natal + return side by side; "single" shows
        only the return chart. An optional return_location relocates
        the return chart to a different city.

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        # REST parity (PlanetaryReturnRequestModel): a search anchor is
        # required, month needs a year, and a day without a month would
        # otherwise be silently ignored by the year-only search branch.
        try:
            if year is None and iso_datetime is None:
                return {"status": "ERROR", "message": "Provide either 'iso_datetime' or 'year' (with optional month and day) to locate the return."}
            if month is not None and year is None:
                return {"status": "ERROR", "message": "Month can only be provided together with a year."}
            if day is not None and day != 1 and month is None:
                return {"status": "ERROR", "message": "Day can only be provided together with month and year."}

            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=resolved_points)
            return_factory = await run_heavy(_build_return_factory_from_model, natal_subject, return_location, subject_input=subject)

            backwards = direction == "previous"
            if iso_datetime:
                return_subject = await run_heavy(
                    return_factory.next_return_from_iso_formatted_time,
                    iso_datetime,
                    "Solar",
                    backwards=backwards,
                )
            elif month is not None:
                return_subject = await run_heavy(
                    return_factory.next_return_from_date,
                    year,
                    month,
                    day or 1,
                    return_type="Solar",
                    backwards=backwards,
                )
            else:
                return_subject = await run_heavy(
                    return_factory.next_return_from_date,
                    year,
                    1,
                    1,
                    return_type="Solar",
                    backwards=backwards,
                )

            if wheel_type == "dual":
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "DualReturnChart",
                    natal_subject,
                    return_subject,
                    include_house_comparison=include_house_comparison,
                    **_chart_data_kwargs(
                        active_points=resolved_points,
                        active_aspects=resolved_aspects,
                        axis_orb_limit=axis_orb_limit,
                        point_orb_adjustments=point_orb_adjustments,
                        point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                        distribution_method=distribution_method,
                        custom_distribution_weights=custom_distribution_weights,
                    ),
                )
            else:
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "SingleReturnChart",
                    return_subject,
                    **_chart_data_kwargs(
                        active_points=resolved_points,
                        active_aspects=resolved_aspects,
                        axis_orb_limit=axis_orb_limit,
                        point_orb_adjustments=point_orb_adjustments,
                        point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                        distribution_method=distribution_method,
                        custom_distribution_weights=custom_distribution_weights,
                    ),
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )
            elif include_ai_context:
                payload = await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)
            else:
                payload = await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)

            # REST parity (charts.py / context.py solar-return handlers): echo the
            # return kind and wheel configuration alongside the chart payload.
            payload["return_type"] = "Solar"
            payload["wheel_type"] = wheel_type
            return payload
        except Exception as exc:
            logger.error("get_solar_return failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 8
    @mcp.tool()
    async def get_lunar_return(
        subject: MCPSubjectInput,
        year: Optional[int] = None,
        month: Annotated[Optional[int], Field(ge=1, le=12)] = None,
        day: Annotated[Optional[int], Field(ge=1, le=31)] = None,
        iso_datetime: Optional[str] = None,
        direction: Literal["next", "previous"] = "next",
        # Return options
        wheel_type: Literal["dual", "single"] = "dual",
        return_location: Optional[MCPReturnLocationInput] = None,
        include_house_comparison: bool = True,
        # Output options
        include_ai_context: bool = True,
        include_svg: bool = False,
        # Chart rendering
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
        colors_settings: Optional[dict[str, str]] = None,
        language_pack: Optional[dict[str, str]] = None,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        distribution_method: Optional[str] = None,
        custom_distribution_weights: Optional[dict[str, float]] = None,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[dict[str, float]] = None,
        point_orb_adjustment_strategy: Literal["max_explicit", "min_explicit", "sum", "none"] = "max_explicit",
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate a lunar return chart for a given year and month.

        A lunar return occurs when the transiting Moon returns to its exact
        natal longitude (approximately every 27.3 days). Provide either
        iso_datetime, or year + month, to narrow the search window.

        wheel_type "dual" shows natal + return; "single" shows return only.
        An optional return_location relocates the chart.

        Output precedence: include_svg=True returns the rendered SVG payload
        and include_ai_context is ignored; the AI context is only returned
        when include_svg=False.
        """
        # A search anchor is required: iso_datetime, or year + month (the
        # ~27.3-day lunar cycle needs a month to narrow the window).
        try:
            if iso_datetime is None and (year is None or month is None):
                return {"status": "ERROR", "message": "Provide either 'iso_datetime' or both 'year' and 'month' to locate the lunar return."}
            # REST parity (PlanetaryReturnRequestModel): a day without a month
            # would otherwise be silently ignored.
            if day is not None and day != 1 and month is None:
                return {"status": "ERROR", "message": "Day can only be provided together with month and year."}

            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            natal_subject = await run_heavy(_build_subject_from_model, subject, active_points=resolved_points)
            return_factory = await run_heavy(_build_return_factory_from_model, natal_subject, return_location, subject_input=subject)

            backwards = direction == "previous"
            if iso_datetime:
                return_subject = await run_heavy(
                    return_factory.next_return_from_iso_formatted_time,
                    iso_datetime,
                    "Lunar",
                    backwards=backwards,
                )
            else:
                return_subject = await run_heavy(
                    return_factory.next_return_from_date,
                    year,
                    month,
                    day or 1,
                    return_type="Lunar",
                    backwards=backwards,
                )

            if wheel_type == "dual":
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "DualReturnChart",
                    natal_subject,
                    return_subject,
                    include_house_comparison=include_house_comparison,
                    **_chart_data_kwargs(
                        active_points=resolved_points,
                        active_aspects=resolved_aspects,
                        axis_orb_limit=axis_orb_limit,
                        point_orb_adjustments=point_orb_adjustments,
                        point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                        distribution_method=distribution_method,
                        custom_distribution_weights=custom_distribution_weights,
                    ),
                )
            else:
                chart_data = await run_heavy(
                    ChartDataFactory.create_chart_data,
                    "SingleReturnChart",
                    return_subject,
                    **_chart_data_kwargs(
                        active_points=resolved_points,
                        active_aspects=resolved_aspects,
                        axis_orb_limit=axis_orb_limit,
                        point_orb_adjustments=point_orb_adjustments,
                        point_orb_adjustment_strategy=point_orb_adjustment_strategy,
                        distribution_method=distribution_method,
                        custom_distribution_weights=custom_distribution_weights,
                    ),
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
                    colors_settings=colors_settings,
                    language_pack=language_pack,
                    omit_nulls=omit_nulls,
                )
            elif include_ai_context:
                payload = await run_heavy(context_payload, chart_data, omit_nulls=omit_nulls)
            else:
                payload = await run_heavy(chart_data_payload, chart_data, omit_nulls=omit_nulls)

            # REST parity (charts.py / context.py lunar-return handlers): echo the
            # return kind and wheel configuration alongside the chart payload.
            payload["return_type"] = "Lunar"
            payload["wheel_type"] = wheel_type
            return payload
        except Exception as exc:
            logger.error("get_lunar_return failed | exception=%s", type(exc).__name__)
            raise

    # ------------------------------------------------------------------ 9
    @mcp.tool()
    async def get_compatibility_score(
        first_subject: MCPSubjectInput,
        second_subject: MCPSubjectInput,
        # Computation
        active_points: Optional[list[str]] = None,
        active_aspects: Optional[list[dict]] = None,
        # Output
        include_ai_context: bool = True,
        omit_nulls: bool = True,
    ) -> dict:
        """Calculate a Ciro Discepolo compatibility score between two subjects.

        Returns a numeric score, a textual description, a destiny-sign flag,
        the scored aspects, a score breakdown, and the full synastry chart
        data (``chart_data``) — the same shape as the REST
        ``/api/v6/compatibility-score`` endpoint.
        """
        try:
            resolved_points = _resolve_active_points(active_points)
            resolved_aspects = _resolve_active_aspects(active_aspects)

            subj1 = await run_heavy(_build_subject_from_model, first_subject, active_points=resolved_points)
            subj2 = await run_heavy(_build_subject_from_model, second_subject, active_points=resolved_points)

            chart_data = await run_heavy(
                ChartDataFactory.create_synastry_chart_data,
                subj1,
                subj2,
                active_points=resolved_points,
                active_aspects=resolved_aspects,
                include_house_comparison=True,
                include_relationship_score=True,
            )

            if not chart_data.relationship_score:
                raise ValueError("Relationship score computation failed")

            # REST parity (/api/v6/compatibility-score): score fields + the full
            # synastry chart data, not just the two subject dumps.
            result = {
                "status": "OK",
                "score": chart_data.relationship_score.score_value,
                "score_description": chart_data.relationship_score.score_description,
                "is_destiny_sign": chart_data.relationship_score.is_destiny_sign,
                "aspects": dump(chart_data.relationship_score.aspects, omit_nulls=omit_nulls),
                "score_breakdown": dump(chart_data.relationship_score.score_breakdown, omit_nulls=omit_nulls),
                "chart_data": dump(chart_data, omit_nulls=omit_nulls),
            }
            if include_ai_context:
                result["context"] = await run_heavy(to_context, chart_data)
            return result
        except Exception as exc:
            logger.error("get_compatibility_score failed | exception=%s", type(exc).__name__)
            raise
