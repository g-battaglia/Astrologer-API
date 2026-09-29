from __future__ import annotations

import functools
import inspect
import json
from datetime import datetime, timezone
from logging import getLogger
from typing import Any, Literal, Optional, Sequence, Union, Callable, cast

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    MoonPhaseDetailsFactory,
    to_context,
)
from kerykeion import PlanetaryReturnFactory
from kerykeion.schemas import ActiveAspect, AstrologicalPoint, AstrologicalSubjectModel, KerykeionException
from kerykeion.schemas import SingleChartDataModel, DualChartDataModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

from kerykeion.schemas import MoonPhaseOverviewModel

from .heavy_work import ServerBusyError, run_heavy  # noqa: F401 - compatibility re-export
from .logging_utils import get_request_id, log_exception
from .rendering_validation import validate_colors_settings, validate_language_pack
from ..types.request_models import (
    DEFAULT_NAKSHATRA_AYANAMSA,
    _ENGINE_RETURN_FACTORY_ACCEPTS_NAKSHATRA_AYANAMSA,
    BirthChartDataRequestModel,
    BirthChartRequestModel,
    CompositeChartDataRequestModel,
    CompositeChartRequestModel,
    MoonPhaseRequestModel,
    PlanetaryReturnDataRequestModel,
    PlanetaryReturnRequestModel,
    SubjectModel,
    SynastryChartDataRequestModel,
    SynastryChartRequestModel,
    TransitChartDataRequestModel,
    TransitChartRequestModel,
    _normalize_active_points,
)

logger = getLogger(__name__)


def iso_utc(moment: datetime) -> str:
    """ISO-8601 string in UTC."""
    return moment.astimezone(timezone.utc).isoformat()


def iso_utc_opt(moment: Optional[datetime]) -> Optional[str]:
    """ISO-8601 string in UTC, or ``None``."""
    return iso_utc(moment) if moment is not None else None


def local_iso(moment: datetime, tz: Any) -> str:
    """Full ISO-8601 datetime rendered in the given local timezone.

    Unlike :func:`local_hm`, this keeps the calendar date, so it is unambiguous
    for windows that may span more than one day (e.g. a void-of-course period).
    """
    return moment.astimezone(tz).isoformat()


def local_hm(moment: Optional[datetime], tz: Any) -> Optional[str]:
    """Local ``HH:MM`` rendering of a UTC datetime, ROUNDED, or ``None``.

    Use only when the moment is known to fall on a single, caller-known civil
    date (e.g. sunrise/sunset for a requested date); otherwise prefer
    :func:`local_iso`, which carries the date.

    Rounded to the nearest minute, not truncated. ``strftime("%H:%M")`` discards
    the seconds, so a sunrise at 05:13:39 printed as ``05:13`` while every
    published table prints ``05:14`` — an error of up to 59 s that lands on
    roughly half of all values, and the only part of the sun-times payload a
    user actually reads. The engine's own instants were never wrong; this is
    purely how they were rendered.

    Done on the local wall-clock fields rather than by adding 30 s to the
    datetime: adding a timedelta to an aware datetime is wall-clock arithmetic,
    and re-resolving the offset at the new clock time is exactly the kind of
    DST-boundary surprise this codebase has been bitten by before. It does not
    make the rendering exact across a DST transition — ``02:59:30`` on either
    side of a fall-back both render ``03:00`` — but the events this is used for
    do not land there.

    ROUNDING NEVER CARRIES PAST MIDNIGHT. A first version let it wrap, and a
    sunset at 23:59:45 local rendered ``00:00``. Reachable deterministically:
    latitude is a request parameter, so some latitude puts sunset in that
    30-second window on any date (measured at 64.868 N, 2026-06-10,
    Europe/Helsinki). So the last minute of the day clamps to ``23:59``: inside
    that 30-second window the rendering error goes back up to 30-60 s, which is
    the cost of not INVENTING a next-day reading out of a same-day instant.

    IT DOES NOT, AND CANNOT, GUARANTEE THAT THE VALUE BELONGS TO THE REQUESTED
    DATE. An earlier version of this note claimed it did. At high latitude the
    sunset instant is genuinely past local midnight, and no rendering rule can
    fix that — an ``HH:MM`` field has nowhere to put the date. Measured for June
    2026: Fairbanks 30 days out of 30 and Nome 30/30 report a ``sunset_local``
    EARLIER than that day's ``sunrise_local`` (rise ``03:00``, set ``00:44``);
    Reykjavik 12/30. The instant is correct and the ISO ``sunset`` field carries
    the real date; only the short string cannot say so. Callers rendering these
    two side by side at |lat| > 60 must read the ISO fields or
    :func:`local_iso`, not this one.
    """
    if moment is None:
        return None
    local = moment.astimezone(tz)
    minutes = local.hour * 60 + local.minute + (1 if local.second >= 30 else 0)
    minutes = min(minutes, 1439)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


GEONAMES_HINT = (
    "You can create a free GeoNames username at https://www.geonames.org/login/. To bypass GeoNames, provide latitude, longitude, and timezone directly and remove the geonames_username field."
)

_SUBJECT_LOCATION_PATHS = (
    ("subject",),
    ("first_subject",),
    ("second_subject",),
    ("transit_subject",),
    ("return_location",),
)


def normalize_coordinate(value: Optional[float]) -> Optional[float]:
    """
    Normalize coordinate values to avoid zero division or other numerical issues.
    Values close to zero are adjusted to +/- 1e-6.
    """
    if value is None:
        return None
    if abs(value) < 1e-6:
        return 1e-6 if value >= 0 else -1e-6
    return value


def dump(value: object, *, omit_nulls: bool = False) -> object:
    """Recursively dump Pydantic models to dictionaries."""
    if isinstance(value, list):
        return [dump(item, omit_nulls=omit_nulls) for item in value]
    if isinstance(value, tuple):
        return tuple(dump(item, omit_nulls=omit_nulls) for item in value)
    # mode="json": render datetime/timedelta/etc. as JSON-native primitives
    # (ISO-8601 strings / ISO durations) so Starlette's JSONResponse — which has
    # no custom encoder — can serialise kerykeion models that carry native
    # date/time values (e.g. MoonPhaseSunInfoModel since kerykeion a59).
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True, mode="json") if omit_nulls else value.model_dump(mode="json")
    return value


def resolve_nation(value: Optional[str]) -> Optional[str]:
    """Resolve nation code to uppercase or None."""
    if not value or value.lower() == "null":
        return None
    return value.upper()


def resolve_active_points(points: Optional[Sequence[str]]) -> list[AstrologicalPoint]:
    """Resolve active points, falling back to defaults if not provided."""
    if points:
        return cast(list[AstrologicalPoint], _normalize_active_points(list(points)) or [])
    return list(DEFAULT_ACTIVE_POINTS)


def resolve_active_aspects(
    aspects: Optional[Sequence[ActiveAspect]],
) -> Optional[list[ActiveAspect]]:
    """Resolve active aspects from a request.

    Returns ``None`` when the caller did not specify aspects, so the kerykeion
    ``ChartDataFactory`` applies its per-chart-type default (natal orbs for
    natal/synastry/composite, the tight predictive orbs for transit/return/
    progression). Returning a fixed natal default here would force natal-wide
    orbs onto predictive charts.
    """
    if aspects:
        return [cast(ActiveAspect, dict(aspect)) for aspect in aspects]
    return None


def _extract_v6_calculation_config(subject_request: SubjectModel) -> dict:
    """Extract v6 calculation configuration kwargs from a SubjectModel."""
    kwargs: dict = {}
    if subject_request.calculate_dignities:
        kwargs["calculate_dignities"] = True
    if subject_request.calculate_nakshatra:
        kwargs["calculate_nakshatra"] = True
    if subject_request.calculate_gauquelin:
        kwargs["calculate_gauquelin"] = True
    if subject_request.calculate_nutation:
        kwargs["calculate_nutation"] = True
    if subject_request.calculate_local_space:
        kwargs["calculate_local_space"] = True
    if subject_request.active_fixed_stars:
        kwargs["active_fixed_stars"] = subject_request.active_fixed_stars
    add_nakshatra_ayanamsa_kwarg(kwargs, subject_request)
    return kwargs


def add_nakshatra_ayanamsa_kwarg(kwargs: dict, request_body: object) -> None:
    """Forward ``nakshatra_ayanamsa`` only when it differs from the engine default.

    Same deploy-ahead rule as ``EXTENDED_RENDERING_FIELDS``: an engine that
    predates the keyword raises ``TypeError`` inside the factory, which is not a
    degraded feature but a 500 on *every* request that builds a subject —
    including the overwhelming majority that never mention nakshatras. Held back
    at its default, the whole default path keeps working against an older
    runtime; a caller who changes it gets the error only until the pin lands.

    ``None`` is a real, non-default choice here (the uncorrected legacy values),
    so it is forwarded — the test for "unset" is equality with the default, not
    truthiness.
    """
    ayanamsa = getattr(request_body, "nakshatra_ayanamsa", DEFAULT_NAKSHATRA_AYANAMSA)
    if ayanamsa != DEFAULT_NAKSHATRA_AYANAMSA:
        kwargs["nakshatra_ayanamsa"] = ayanamsa


class EngineCapabilityError(KerykeionException):
    """The payload is valid, but the installed calculation engine cannot honor it.

    Nothing about the request is malformed — the very same body succeeds once
    the engine pin lands — so this is neither a client mistake nor a server
    fault, and it must not be reported as either. ``handle_exception`` maps it
    to 422, the status the aspect-keyed-orb capability gate already produces
    from its pydantic validator, so the two capability refusals look alike from
    the outside.
    """


def guard_return_factory_v6_kwargs(kwargs: dict) -> None:
    """Refuse, rather than silently drop, a v6 kwarg the return factory lacks.

    ``_extract_v6_calculation_config`` is shared by the subject path and the
    return path, but the two factories do not necessarily learn a keyword in
    the same engine release: a91 gave ``nakshatra_ayanamsa`` to
    ``AstrologicalSubjectFactory`` first. Splatting the extracted block into a
    ``PlanetaryReturnFactory`` that predates the keyword is a ``TypeError``
    deep inside the constructor, i.e. a 500 on all twelve return endpoints.

    Dropping the key would turn that 500 into something worse: the caller asked
    for the nakshatras to be read off ayanamsa-corrected longitudes, and would
    get them read off uncorrected ones — off by nearly two mansions — while the
    response echoed the ayanamsa they asked for. A refusal is the only answer
    that stays true.

    The default path is untouched: ``add_nakshatra_ayanamsa_kwarg`` only puts the key
    in ``kwargs`` when the caller moved it off the default, so a request that
    never mentions nakshatras keeps working against an older engine.
    """
    if "nakshatra_ayanamsa" in kwargs and not _ENGINE_RETURN_FACTORY_ACCEPTS_NAKSHATRA_AYANAMSA:
        raise EngineCapabilityError(
            "nakshatra_ayanamsa is not supported by this engine version for return charts. "
            "Omit the field to let the return subject use the engine's default ayanamsa, "
            "or upgrade the calculation engine."
        )


def build_subject(subject_request: SubjectModel, *, active_points: Optional[Sequence[str]] = None) -> AstrologicalSubjectModel:
    """Build an AstrologicalSubject instance from a request model.

    If the request includes ``active_midpoints``, the resulting subject is
    post-populated with synthetic midpoint points so the chart drawer can
    render them on the wheel.
    """
    resolved_points = resolve_active_points(active_points)
    online = bool(subject_request.geonames_username)

    subject = AstrologicalSubjectFactory.from_birth_data(
        name=subject_request.name,
        year=subject_request.year,
        month=subject_request.month,
        day=subject_request.day,
        hour=subject_request.hour,
        minute=subject_request.minute,
        seconds=subject_request.second or 0,
        city=subject_request.city,
        nation=resolve_nation(subject_request.nation) or "GB",
        lng=subject_request.longitude,
        lat=subject_request.latitude,
        tz_str=subject_request.timezone,
        geonames_username=subject_request.geonames_username,
        online=online,
        zodiac_type=subject_request.zodiac_type or "Tropical",
        sidereal_mode=subject_request.sidereal_mode,
        houses_system_identifier=subject_request.houses_system_identifier or "P",
        perspective_type=subject_request.perspective_type or "Apparent Geocentric",
        is_dst=subject_request.is_dst,
        altitude=subject_request.altitude,
        active_points=resolved_points,
        suppress_geonames_warning=True,
        custom_ayanamsa_t0=subject_request.custom_ayanamsa_t0,
        custom_ayanamsa_ayan_t0=subject_request.custom_ayanamsa_ayan_t0,
        **_extract_v6_calculation_config(subject_request),
    )

    midpoint_pairs = getattr(subject_request, "active_midpoints", None)
    if midpoint_pairs:
        from kerykeion import MidpointFactory  # local import keeps cold path light

        subject.active_midpoints = MidpointFactory.compute_active_midpoint_points(subject, midpoint_pairs)

    return subject


def _extract_v6_now_config(request_body) -> dict:
    """Extract v6 calculation config kwargs from a NowSubjectDefinitionModel."""
    kwargs: dict = {}
    if getattr(request_body, "calculate_dignities", False):
        kwargs["calculate_dignities"] = True
    if getattr(request_body, "calculate_nakshatra", False):
        kwargs["calculate_nakshatra"] = True
    if getattr(request_body, "calculate_gauquelin", False):
        kwargs["calculate_gauquelin"] = True
    if getattr(request_body, "calculate_nutation", False):
        kwargs["calculate_nutation"] = True
    if getattr(request_body, "calculate_local_space", False):
        kwargs["calculate_local_space"] = True
    if getattr(request_body, "active_fixed_stars", None):
        kwargs["active_fixed_stars"] = request_body.active_fixed_stars
    add_nakshatra_ayanamsa_kwarg(kwargs, request_body)
    return kwargs


def build_now_subject(request_body, utc_datetime) -> object:
    """Build an AstrologicalSubject for the current UTC time at Greenwich."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        name=request_body.name,
        year=utc_datetime.year,
        month=utc_datetime.month,
        day=utc_datetime.day,
        hour=utc_datetime.hour,
        minute=utc_datetime.minute,
        seconds=utc_datetime.second,
        city="Greenwich",
        nation="GB",
        lng=-0.001545,
        lat=51.477928,
        tz_str="Etc/UTC",
        online=False,
        # Explicit null in the JSON body reaches here as None — fall back like
        # build_subject does, or kerykeion's normalizer raises on None (500).
        zodiac_type=request_body.zodiac_type or "Tropical",
        sidereal_mode=request_body.sidereal_mode,
        perspective_type=request_body.perspective_type,
        houses_system_identifier=request_body.houses_system_identifier,
        custom_ayanamsa_t0=getattr(request_body, "custom_ayanamsa_t0", None),
        custom_ayanamsa_ayan_t0=getattr(request_body, "custom_ayanamsa_ayan_t0", None),
        active_points=resolve_active_points(getattr(request_body, "active_points", None)),
        suppress_geonames_warning=True,
        **_extract_v6_now_config(request_body),
    )

    midpoint_pairs = getattr(request_body, "active_midpoints", None)
    if midpoint_pairs:
        from kerykeion import MidpointFactory

        subject.active_midpoints = MidpointFactory.compute_active_midpoint_points(subject, midpoint_pairs)

    return subject


def build_transit_subject(
    transit_request,
    reference_subject,
    *,
    active_points: Optional[Sequence[str]] = None,
    custom_ayanamsa_t0: Optional[float] = None,
    custom_ayanamsa_ayan_t0: Optional[float] = None,
    natal_subject_request: Optional[SubjectModel] = None,
) -> AstrologicalSubjectModel:
    """Build a Transit Subject instance, inheriting settings from a reference subject.

    v6 calculation flags are inherited from the natal subject request when provided.
    """
    resolved_points = resolve_active_points(active_points)
    online = bool(transit_request.geonames_username)

    v6_kwargs = _extract_v6_calculation_config(natal_subject_request) if natal_subject_request else {}

    return AstrologicalSubjectFactory.from_birth_data(
        name=transit_request.name or "Transit",
        year=transit_request.year,
        month=transit_request.month,
        day=transit_request.day,
        hour=transit_request.hour,
        minute=transit_request.minute,
        seconds=transit_request.second or 0,
        city=transit_request.city,
        nation=resolve_nation(transit_request.nation) or reference_subject.nation,
        lng=transit_request.longitude,
        lat=transit_request.latitude,
        tz_str=transit_request.timezone,
        geonames_username=transit_request.geonames_username,
        online=online,
        zodiac_type=reference_subject.zodiac_type,
        sidereal_mode=reference_subject.sidereal_mode,
        houses_system_identifier=reference_subject.houses_system_identifier,
        perspective_type=reference_subject.perspective_type,
        is_dst=transit_request.is_dst,
        altitude=transit_request.altitude,
        active_points=resolved_points,
        suppress_geonames_warning=True,
        custom_ayanamsa_t0=custom_ayanamsa_t0,
        custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
        **v6_kwargs,
    )


@functools.lru_cache(maxsize=8)
def _drawer_supports_diurnality(drawer: Callable[..., Any]) -> bool:
    """True when the installed kerykeion ``ChartDrawer`` accepts ``show_diurnality``.

    The parameter arrived in kerykeion 6.0.0a78. Passing it unconditionally to an
    older runtime is not a degraded feature but a total outage: ``__init__``
    raises ``TypeError`` and *every* SVG endpoint returns 500, including requests
    that never mention the flag.

    Degrading is exact rather than approximate, which is why this needs no error
    path. A runtime without the parameter draws no diurnality line at all, and
    that is precisely what ``show_diurnality=False`` asks for; the default
    ``True`` simply has nothing to switch on. Same probe idiom as
    ``_ephemeris_factory_supports_fixed_stars``, cached per object so a
    monkeypatched drawer in a test gets its own entry.
    """
    try:
        return "show_diurnality" in inspect.signature(drawer).parameters
    except (TypeError, ValueError):  # non-introspectable callable: assume legacy
        return False


# Every ChartDrawer-facing rendering option, name → default. The three
# functions below iterate this instead of restating the list, so a new option
# is one entry here plus one field on ``ChartRenderingMixin``. ``theme``,
# ``language`` and ``split_chart`` stay out: the first two are renamed on the
# way to the drawer and the third selects which SVGs come back, not how they
# are drawn.
RENDERING_FIELD_DEFAULTS: dict[str, Any] = {
    "transparent_background": False,
    "show_house_position_comparison": True,
    "show_cusp_position_comparison": True,
    "show_degree_indicators": True,
    "show_aspect_icons": True,
    "custom_title": None,
    "style": "classic",
    "glyph_size": "medium",
    "show_zodiac_background_ring": True,
    "double_chart_aspect_grid_type": "list",
    "auto_size": True,
    "padding": 20,
    "colors_settings": None,
    "language_pack": None,
    "external_view": False,
    "show_diurnality": True,
    "show_motion_state": False,
    "show_out_of_bounds": False,
    "show_aspect_movement": False,
    "show_relationship_score": False,
    "show_ayanamsa_value": False,
    "show_polar_fallback_note": False,
}

# Forwarded to ChartDrawer only when the caller asks for something other than
# the default. The pinned kerykeion does not know these keywords yet, and an
# unknown keyword is not a degraded feature but a total outage: ``__init__``
# raises TypeError and every SVG endpoint returns 500, including requests that
# never mention the option. Omitted at its default the whole default path stays
# intact; a caller that changes one gets the error until the pin moves — same
# reasoning as ``_drawer_supports_diurnality``, without the probe, because the
# default render never needs the keyword.
#
# The rule is "omitted when equal to its default", not "omitted when false":
# the set is no longer all-boolean. ``glyph_size`` is a three-valued enum whose
# default, "medium", is truthy, so anything reading these by truthiness sends
# ``glyph_size=True`` to the drawer.
EXTENDED_RENDERING_FIELDS = frozenset(
    {
        "glyph_size",
        "show_motion_state",
        "show_out_of_bounds",
        "show_aspect_movement",
        "show_relationship_score",
        "show_ayanamsa_value",
        "show_polar_fallback_note",
    }
)


def render_chart(
    chart_data,
    theme: Optional[str],
    language: Optional[str],
    split_chart: bool = False,
    **rendering: Any,
) -> dict:
    """Render chart(s) based on configuration.

    Rendering options are named in :data:`RENDERING_FIELD_DEFAULTS`; whatever the
    caller omits takes its default from there.
    """
    unknown = rendering.keys() - RENDERING_FIELD_DEFAULTS.keys()
    if unknown:
        # ``**rendering`` would otherwise swallow a misspelled option in silence,
        # where the previous explicit signature raised TypeError.
        raise TypeError(f"render_chart() got unexpected keyword argument(s): {', '.join(sorted(unknown))}")

    options = {**RENDERING_FIELD_DEFAULTS, **rendering}

    colors_settings = validate_colors_settings(options["colors_settings"])
    if colors_settings is None:
        del options["colors_settings"]
    else:
        # ChartDrawer replaces its color table wholesale and indexes it by key,
        # so a partial override ({"paper_0": "#fff"}) would KeyError mid-render
        # (500). Merge over the defaults so partial overrides are valid.
        from kerykeion.settings import DEFAULT_CHART_COLORS

        options["colors_settings"] = {**DEFAULT_CHART_COLORS, **colors_settings}

    language_pack = validate_language_pack(options["language_pack"])
    if language_pack is None:
        del options["language_pack"]
    else:
        options["language_pack"] = language_pack

    if not _drawer_supports_diurnality(ChartDrawer):
        del options["show_diurnality"]

    for name in EXTENDED_RENDERING_FIELDS:
        if options[name] == RENDERING_FIELD_DEFAULTS[name]:
            del options[name]

    drawer = ChartDrawer(
        chart_data=chart_data,
        theme=theme or "classic",
        chart_language=language or "EN",
        **options,
    )

    if split_chart:
        return {
            "chart_wheel": drawer.generate_wheel_only_svg_string(minify=True),
            "chart_grid": drawer.generate_aspect_grid_only_svg_string(minify=True),
        }
    return {"chart": drawer.generate_svg_string(minify=True)}


def _lift_composite_fields(serialized: object) -> None:
    """Lift first_subject, second_subject, and composite_chart_type from
    subject to the top level of chart_data for V5 backward compatibility.

    In Kerykeion V6 the CompositeSubjectModel nests these fields inside
    ``subject``.  V5 exposed them as siblings of ``subject`` in
    ``chart_data``.  Consumers (Astrologer Studio, RapidAPI users, etc.)
    rely on the V5 layout, so we copy them up here.
    """
    if not isinstance(serialized, dict):
        return
    if serialized.get("chart_type") != "Composite":
        return

    subject = serialized.get("subject")
    if not isinstance(subject, dict):
        return

    # house_anchor and house_frame (kerykeion a87) ride along so the composite's
    # provenance sits beside composite_chart_type at both levels.
    for key in ("first_subject", "second_subject", "composite_chart_type", "house_anchor", "house_frame"):
        if key in subject:
            serialized[key] = subject[key]


def chart_data_payload(chart_data, *, omit_nulls: bool = False) -> dict:
    """Wrap chart data in a standard response payload."""
    serialized = dump(chart_data, omit_nulls=omit_nulls)
    _lift_composite_fields(serialized)
    return {
        "status": "OK",
        "chart_data": serialized,
    }


def chart_payload(
    chart_data,
    theme: Optional[str],
    language: Optional[str],
    split_chart: bool = False,
    *,
    omit_nulls: bool = False,
    **rendering: Any,
) -> dict:
    """Generate a complete chart payload including data and rendered SVG(s)."""
    payload = chart_data_payload(chart_data, omit_nulls=omit_nulls)
    payload.update(render_chart(chart_data, theme, language, split_chart, **rendering))
    return payload


def chart_payload_from_request(chart_data, request_body) -> dict:
    """Generate chart payload extracting all rendering params from a request model."""
    return chart_payload(
        chart_data,
        getattr(request_body, "theme", "classic"),
        getattr(request_body, "language", "EN"),
        getattr(request_body, "split_chart", False),
        **{name: getattr(request_body, name, default) for name, default in RENDERING_FIELD_DEFAULTS.items()},
    )


def subject_context_payload(subject, *, omit_nulls: bool = False) -> dict:
    """Wrap subject data with AI-optimized context in a standard response payload."""
    return {
        "status": "OK",
        "context": to_context(subject),
        "subject": dump(subject, omit_nulls=omit_nulls),
    }


def context_payload(chart_data, *, omit_nulls: bool = False) -> dict:
    """Wrap chart data with AI-optimized context in a standard response payload."""
    serialized = dump(chart_data, omit_nulls=omit_nulls)
    _lift_composite_fields(serialized)
    return {
        "status": "OK",
        "context": to_context(chart_data),
        "chart_data": serialized,
    }


_SINGLE_CHART_TYPES = frozenset({"Natal", "Composite", "SingleReturnChart"})
_DUAL_CHART_TYPES = frozenset({"Transit", "Synastry", "DualReturnChart"})


def parse_precomputed_chart_data(
    raw: dict[str, Any],
) -> Union[SingleChartDataModel, DualChartDataModel]:
    """Parse a raw chart_data dict into the appropriate Kerykeion model.

    Accepts the same ``chart_data`` object returned by ``/chart/*`` and
    ``/context/*`` responses.  Extra fields not defined on the model are
    silently ignored (Kerykeion models use Pydantic's default
    ``extra="ignore"``).

    Raises ``KerykeionException`` (→ 400) when ``chart_type`` is missing or
    unrecognized, or when the supplied ``chart_data`` fails model validation —
    both are client-input errors, not server faults, so they must not surface
    as an HTTP 500.
    """
    chart_type = raw.get("chart_type", "")
    if chart_type not in _SINGLE_CHART_TYPES and chart_type not in _DUAL_CHART_TYPES:
        raise KerykeionException(f"Unrecognized chart_type: '{chart_type}'. Expected one of: {', '.join(sorted(_SINGLE_CHART_TYPES | _DUAL_CHART_TYPES))}")
    model = SingleChartDataModel if chart_type in _SINGLE_CHART_TYPES else DualChartDataModel
    try:
        return model.model_validate(raw)
    except PydanticValidationError as exc:
        raise KerykeionException(f"Malformed chart_data for chart_type '{chart_type}': {exc.error_count()} validation error(s).") from exc


def _classify_geonames_error(message: str) -> Optional[str]:
    """Classify a GeoNames-related error from the exception message.

    Returns one of: ``"city_not_found"``, ``"timeout"``,
    ``"connection_error"``, ``"missing_coordinates"``, or ``None``.
    """
    city_not_found_markers = (
        "Missing data from geonames",
        "No data found for this city",
        "data found for this city",
    )
    if any(m in message for m in city_not_found_markers):
        return "city_not_found"

    if "ConnectTimeout" in message or "ReadTimeout" in message:
        return "timeout"

    if "ConnectionError" in message or "Check your connection" in message:
        return "connection_error"

    if "You need to set the coordinates" in message:
        return "missing_coordinates"

    return None


def _extract_location_from_body(body_str: str) -> tuple[Optional[str], Optional[str]]:
    """Try to extract ``(city, nation)`` from a JSON request body.

    Walks the known subject paths (``subject``, ``first_subject``,
    ``second_subject``, ``transit_subject``, ``return_location``) and
    returns the city/nation from the first entry that has
    ``geonames_username`` set.
    """
    try:
        body = json.loads(body_str)
    except (json.JSONDecodeError, TypeError):
        return None, None

    if not isinstance(body, dict):
        return None, None

    for path in _SUBJECT_LOCATION_PATHS:
        node = body.get(path[0])
        if not isinstance(node, dict):
            continue
        if node.get("geonames_username"):
            return node.get("city"), node.get("nation")

    # Fallback: first subject with city/nation regardless of geonames
    for path in _SUBJECT_LOCATION_PATHS:
        node = body.get(path[0])
        if isinstance(node, dict) and node.get("city"):
            return node.get("city"), node.get("nation")

    return None, None


def _build_geonames_error_response(
    error_category: str,
    city: Optional[str],
    nation: Optional[str],
) -> tuple[int, dict]:
    """Return ``(status_code, response_dict)`` for a GeoNames error."""

    location_hint = ""
    if city or nation:
        parts = []
        if city:
            parts.append(f"city='{city}'")
        if nation:
            parts.append(f"nation='{nation}'")
        location_hint = f" for {', '.join(parts)}"

    if error_category == "city_not_found":
        msg = (
            f"No location data found{location_hint}. "
            "Verify the city name spelling and ensure the nation code matches "
            "the country where the city is located. The nation field uses "
            "ISO 3166-1 alpha-2 country codes (e.g. 'EG' for Egypt, 'US' for United States)."
        )
        status_code = 400
    elif error_category == "timeout":
        msg = f"GeoNames API timed out while resolving{location_hint}. The service may be temporarily overloaded. Please retry in a few moments."
        status_code = 504
    elif error_category == "connection_error":
        msg = f"Unable to reach the GeoNames API while resolving{location_hint}. Please retry later."
        status_code = 502
    elif error_category == "missing_coordinates":
        msg = "You need to provide coordinates (latitude, longitude) and timezone for offline mode, or include a geonames_username for online resolution."
        status_code = 400
    else:
        msg = f"GeoNames lookup failed{location_hint}. Please check the city name, nation code, and your GeoNames username."
        status_code = 400

    details = {"error_category": error_category}
    if city:
        details["city"] = city
    if nation:
        details["nation"] = nation

    return status_code, {
        "status": "ERROR",
        "message": msg,
        "error_type": "GeoNamesLookupError",
        "details": details,
        "hint": GEONAMES_HINT,
    }


async def handle_exception(exc: Exception, request: Request) -> JSONResponse:
    """Handle exceptions and return appropriate JSON responses.

    GeoNames errors get contextual messages with city/nation details and are
    logged at WARNING level. All other errors are logged at ERROR with full
    traceback.
    """
    message = str(exc).strip() or exc.__class__.__name__

    # The body is read only for the GeoNames response enrichment below. It is
    # never logged: names, cities, coordinates and birth times are personal data.
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else ""
    except Exception:  # pragma: no cover
        logger.error(
            "request body unavailable | request_id=%s | path=%s",
            get_request_id(request),
            request.url.path,
        )
        body_str = ""

    # --- GeoNames-specific path ---
    geonames_category = _classify_geonames_error(message)
    if geonames_category is not None:
        city, nation = _extract_location_from_body(body_str)
        logger.warning(
            "GeoNames %s | request_id=%s | path=%s",
            geonames_category,
            get_request_id(request),
            request.url.path,
        )
        status_code, content = _build_geonames_error_response(
            geonames_category,
            city,
            nation,
        )
        return JSONResponse(content=content, status_code=status_code)

    # --- Date-range overflow path ---
    # Dates within ~a day of the supported 1-9999 CE bounds can push an
    # adjacent-day or search-window datetime past Python's range (raised deep in
    # the ephemeris / timezone math as OverflowError or "out of range"
    # ValueError). Surface that as a clean client error instead of a 500.
    if isinstance(exc, OverflowError) or (isinstance(exc, ValueError) and "out of range" in message.lower()):
        logger.warning("Date-range overflow | request_id=%s | path=%s", get_request_id(request), request.url.path)
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": ("The requested date is too close to the supported 1-9999 CE boundary for this calculation."),
                "error_type": "DateRangeError",
            },
            status_code=400,
        )

    # --- DST gap/fold path ---
    # A wall-clock time that a DST transition skips or repeats is a property of
    # the client's input, not a server fault, so it earns a 400 carrying the
    # hint that names the way out rather than a logged traceback.
    #
    # Both conditions arrive as a plain KerykeionException and are told apart by
    # the sentence they open with, so the discrimination is on the prefix. That
    # is a weaker hinge than an exception class, which is why the contract is
    # part of the error contract: if the wording ever
    # moves, the test says so instead of this branch going quietly dead.
    #
    # The message is rebuilt rather than interpolated. The exception text is
    # already a full sentence addressed to a library caller, so quoting it
    # inside another sentence reads as two collided errors, and it spells the
    # is_dst values in Python's capitalisation while the client has to send
    # JSON's. Keep this above the generic KerykeionException arm further down,
    # which would otherwise swallow it into an untyped 400.
    if isinstance(exc, KerykeionException) and message.startswith(("Non-existent time error!", "Ambiguous time error!")):
        skipped = message.startswith("Non-existent time error!")
        kind = "does not exist (skipped by the DST jump)" if skipped else "is ambiguous (repeated when DST ends)"
        # A skipped time has no reading to choose between, so the only honest
        # advice is to move it; a repeated one has two, and is_dst picks.
        fix = (
            "Shift the time outside the DST transition, or pass is_dst=true or is_dst=false to accept the adjacent reading."
            if skipped
            else "Pass is_dst=true or is_dst=false to disambiguate, or shift the time outside the DST transition."
        )
        logger.warning("DST gap/fold | request_id=%s | path=%s", get_request_id(request), request.url.path)
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": (f"The requested wall-clock time {kind} in the subject's timezone. {fix}"),
                "error_type": "DstTransitionError",
            },
            status_code=400,
        )

    # --- Ephemeris factory resource-limit path ---
    # Request validation mirrors the factory's sample count, but keep this
    # final guard so a future dependency change cannot turn a bounded client
    # request into an internal 500.
    if isinstance(exc, ValueError) and message.lower().startswith(("too many days:", "too many hours:", "too many minutes:")):
        logger.warning("Ephemeris resource limit | request_id=%s | path=%s", get_request_id(request), request.url.path)
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": message,
                "error_type": "ResourceLimitError",
            },
            status_code=422,
        )

    # --- Bounded heavy-work admission path ---
    if isinstance(exc, ServerBusyError):
        logger.warning("Heavy-work capacity busy | request_id=%s | path=%s", get_request_id(request), request.url.path)
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": "Calculation capacity is currently busy. Retry after a short delay.",
                "error_type": "ServerBusy",
            },
            status_code=503,
            headers={"Retry-After": "2"},
        )

    # --- Engine capability path ---
    # A valid payload the installed engine cannot honor yet. Answered above the
    # generic KerykeionException arm so it earns a 422 and a WARNING instead of
    # an untyped 400 with a full traceback: nothing failed here, the deployment
    # simply runs ahead of its engine, and the log line that matters is which
    # capability was asked for.
    if isinstance(exc, EngineCapabilityError):
        logger.warning("Engine capability refused | request_id=%s | path=%s", get_request_id(request), request.url.path)
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": message,
                "error_type": "EngineCapabilityError",
            },
            status_code=422,
        )

    # --- Generic error path ---
    log_exception(logger, request, "calculation", exc)
    if isinstance(exc, KerykeionException):
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": message,
                "error_type": exc.__class__.__name__,
            },
            status_code=400,
        )
    # Unexpected exception: never leak internal details (paths, library
    # internals) to the client — the full traceback is already logged above.
    return JSONResponse(
        content={
            "status": "ERROR",
            "message": "Internal server error. The failure has been logged.",
            "error_type": "InternalServerError",
        },
        status_code=500,
    )


def build_return_factory(
    natal_subject,
    request_body: Union[PlanetaryReturnRequestModel, PlanetaryReturnDataRequestModel],
) -> PlanetaryReturnFactory:
    """Build a PlanetaryReturnFactory based on request parameters."""
    location = request_body.return_location

    custom_ayanamsa_kwargs: dict = {}
    if hasattr(request_body, "subject") and hasattr(request_body.subject, "custom_ayanamsa_t0"):
        if request_body.subject.custom_ayanamsa_t0 is not None:
            custom_ayanamsa_kwargs["custom_ayanamsa_t0"] = request_body.subject.custom_ayanamsa_t0
        if request_body.subject.custom_ayanamsa_ayan_t0 is not None:
            custom_ayanamsa_kwargs["custom_ayanamsa_ayan_t0"] = request_body.subject.custom_ayanamsa_ayan_t0

    # v6: propagate the natal subject's v6 calc flags (active_fixed_stars,
    # dignities, nakshatra, gauquelin, nutation, local space) so that the
    # return subject computes the same enrichments. Without this, the user
    # asking for active_fixed_stars=["Betelgeuse"] on the natal request
    # would still get a bare return chart.
    v6_calc_kwargs: dict = {}
    if hasattr(request_body, "subject"):
        v6_calc_kwargs = _extract_v6_calculation_config(request_body.subject)
    guard_return_factory_v6_kwargs(v6_calc_kwargs)

    if location:
        nation = resolve_nation(location.nation) or natal_subject.nation

        if location.geonames_username or location.latitude is None or location.longitude is None or location.timezone is None:
            logger.info("Building return factory with GeoNames lookup.")
            return PlanetaryReturnFactory(
                natal_subject,
                city=location.city or natal_subject.city,
                nation=nation,
                online=True,
                geonames_username=location.geonames_username,
                cache_expire_after_days=30,
                altitude=location.altitude,
                **custom_ayanamsa_kwargs,
                **v6_calc_kwargs,
            )

        logger.info("Building return factory with explicit coordinates.")
        return PlanetaryReturnFactory(
            natal_subject,
            city=location.city or natal_subject.city,
            nation=nation,
            lng=normalize_coordinate(location.longitude),
            lat=normalize_coordinate(location.latitude),
            tz_str=location.timezone,
            online=False,
            altitude=location.altitude,
            **custom_ayanamsa_kwargs,
            **v6_calc_kwargs,
        )

    logger.info("Building return factory using the natal subject location.")
    return PlanetaryReturnFactory(
        natal_subject,
        city=natal_subject.city,
        nation=natal_subject.nation,
        lng=normalize_coordinate(natal_subject.lng),
        lat=normalize_coordinate(natal_subject.lat),
        tz_str=natal_subject.tz_str,
        online=False,
        altitude=getattr(natal_subject, "altitude", None),
        **custom_ayanamsa_kwargs,
        **v6_calc_kwargs,
    )


def calculate_return_chart_data(
    request_body: Union[PlanetaryReturnRequestModel, PlanetaryReturnDataRequestModel],
    return_type: Literal["Solar", "Lunar"],
):
    """Calculate return chart data (Solar or Lunar)."""
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)

    natal_subject = build_subject(request_body.subject, active_points=active_points)
    return_factory = build_return_factory(natal_subject, request_body)

    backwards = getattr(request_body, "direction", "next") == "previous"

    if request_body.iso_datetime:
        return_subject = return_factory.next_return_from_iso_formatted_time(request_body.iso_datetime, return_type, backwards=backwards)
    elif request_body.month is not None:
        if request_body.year is None:
            raise KerykeionException("Year must be provided when month is specified.")
        return_subject = return_factory.next_return_from_date(
            request_body.year,
            request_body.month,
            request_body.day or 1,
            return_type=return_type,
            backwards=backwards,
        )
    else:
        if request_body.year is None:
            raise KerykeionException("Year must be provided when iso_datetime is not set.")
        return_subject = return_factory.next_return_from_date(request_body.year, 1, 1, return_type=return_type, backwards=backwards)

    if request_body.wheel_type == "dual":
        chart_data = ChartDataFactory.create_chart_data(
            "DualReturnChart",
            natal_subject,
            return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=request_body.include_house_comparison,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )
    else:
        chart_data = ChartDataFactory.create_chart_data(
            "SingleReturnChart",
            return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

    return chart_data


def _build_return_chart_data(request_body, natal_subject, return_subject, active_points, active_aspects):
    """Shared dual/single return chart-data construction for heliocentric and
    lunar-node-crossing returns."""
    if request_body.wheel_type == "dual":
        return ChartDataFactory.create_chart_data(
            "DualReturnChart",
            natal_subject,
            return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=request_body.include_house_comparison,
            axis_orb_limit=request_body.axis_orb_limit,
            point_orb_adjustments=request_body.point_orb_adjustments,
            point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )
    return ChartDataFactory.create_chart_data(
        "SingleReturnChart",
        return_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        axis_orb_limit=request_body.axis_orb_limit,
        point_orb_adjustments=request_body.point_orb_adjustments,
        point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )


def calculate_heliocentric_return_chart_data(request_body):
    """Compute heliocentric return chart data (compute mode).

    Shared by /chart, /chart-data and /context heliocentric-return endpoints so
    they cannot drift. Heliocentric returns are NOT dispatched through
    calculate_return_chart_data (which only handles Solar/Lunar) — they use the
    dedicated next_heliocentric_return_* factory methods.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    natal_subject = build_subject(request_body.subject, active_points=active_points)
    return_factory = build_return_factory(natal_subject, request_body)
    backwards = getattr(request_body, "direction", "next") == "previous"

    if request_body.iso_datetime:
        return_subject = return_factory.next_heliocentric_return_from_iso_formatted_time(
            planet_name=request_body.planet,
            iso_formatted_time=request_body.iso_datetime,
            backwards=backwards,
        )
    elif not backwards:
        return_subject = return_factory.next_heliocentric_return_from_year(
            planet_name=request_body.planet,
            year=request_body.year,
        )
    else:
        return_subject = return_factory.next_heliocentric_return_from_date(
            planet_name=request_body.planet,
            year=request_body.year,
            month=1,
            day=1,
            backwards=True,
        )

    return _build_return_chart_data(request_body, natal_subject, return_subject, active_points, active_aspects)


def calculate_lunar_node_crossing_chart_data(request_body):
    """Compute lunar node crossing chart data (compute mode).

    Shared by /chart, /chart-data and /context lunar-node-crossing endpoints.
    Uses the dedicated next_lunar_node_crossing_* factory methods (NOT
    calculate_return_chart_data, which only handles Solar/Lunar).
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    natal_subject = build_subject(request_body.subject, active_points=active_points)
    return_factory = build_return_factory(natal_subject, request_body)
    backwards = getattr(request_body, "direction", "next") == "previous"

    if request_body.iso_datetime:
        return_subject = return_factory.next_lunar_node_crossing_from_iso_formatted_time(
            iso_formatted_time=request_body.iso_datetime,
            backwards=backwards,
        )
    elif not backwards:
        return_subject = return_factory.next_lunar_node_crossing_from_year(
            year=request_body.year,
        )
    else:
        return_subject = return_factory.next_lunar_node_crossing_from_date(
            year=request_body.year,
            month=1,
            day=1,
            backwards=True,
        )

    return _build_return_chart_data(request_body, natal_subject, return_subject, active_points, active_aspects)


def create_natal_chart_data(
    request_body: Union[BirthChartRequestModel, BirthChartDataRequestModel],
):
    """Create natal chart data from request."""
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    subject = build_subject(request_body.subject, active_points=active_points)
    chart_data = ChartDataFactory.create_chart_data(
        "Natal",
        subject,
        active_points=active_points,
        active_aspects=active_aspects,
        axis_orb_limit=request_body.axis_orb_limit,
        point_orb_adjustments=request_body.point_orb_adjustments,
        point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_synastry_chart_data(
    request_body: Union[SynastryChartRequestModel, SynastryChartDataRequestModel],
):
    """Create synastry chart data from request."""
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    first_subject = build_subject(request_body.first_subject, active_points=active_points)
    second_subject = build_subject(request_body.second_subject, active_points=active_points)
    chart_data = ChartDataFactory.create_chart_data(
        "Synastry",
        first_subject,
        second_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        include_house_comparison=request_body.include_house_comparison,
        include_relationship_score=request_body.include_relationship_score,
        axis_orb_limit=request_body.axis_orb_limit,
        point_orb_adjustments=request_body.point_orb_adjustments,
        point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_transit_chart_data(
    request_body: Union[TransitChartRequestModel, TransitChartDataRequestModel],
):
    """Create transit chart data from request."""
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    natal_subject = build_subject(request_body.first_subject, active_points=active_points)
    transit_subject = build_transit_subject(
        request_body.transit_subject,
        reference_subject=natal_subject,
        active_points=active_points,
        custom_ayanamsa_t0=request_body.first_subject.custom_ayanamsa_t0,
        custom_ayanamsa_ayan_t0=request_body.first_subject.custom_ayanamsa_ayan_t0,
        natal_subject_request=request_body.first_subject,
    )
    chart_data = ChartDataFactory.create_chart_data(
        "Transit",
        natal_subject,
        transit_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        include_house_comparison=request_body.include_house_comparison,
        axis_orb_limit=request_body.axis_orb_limit,
        point_orb_adjustments=request_body.point_orb_adjustments,
        point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_composite_chart_data(
    request_body: Union[CompositeChartRequestModel, CompositeChartDataRequestModel],
):
    """Create composite chart data from request. Supports both Midpoint and Davison methods."""
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    first_subject = build_subject(request_body.first_subject, active_points=active_points)
    second_subject = build_subject(request_body.second_subject, active_points=active_points)

    composite_factory = CompositeSubjectFactory(
        first_subject,
        second_subject,
        house_anchor=getattr(request_body, "house_anchor", "auto"),
    )

    composite_type = getattr(request_body, "composite_type", "Midpoint")
    if composite_type == "Davison":
        # Davison rebuilds a real subject at the midpoint in space/time, so it
        # needs the custom-ayanamsa pair when the subjects use sidereal_mode='USER'.
        composite_subject = composite_factory.get_davison_composite_subject_model(
            custom_ayanamsa_t0=request_body.first_subject.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=request_body.first_subject.custom_ayanamsa_ayan_t0,
        )
    else:
        composite_subject = composite_factory.get_midpoint_composite_subject_model()

    chart_data = ChartDataFactory.create_chart_data(
        "Composite",
        composite_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        axis_orb_limit=request_body.axis_orb_limit,
        point_orb_adjustments=request_body.point_orb_adjustments,
        point_orb_adjustment_strategy=request_body.point_orb_adjustment_strategy,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_moon_phase_overview(
    request_body: MoonPhaseRequestModel,
) -> MoonPhaseOverviewModel:
    """Build a minimal AstrologicalSubject from flat moon phase request fields
    and compute a detailed moon phase overview."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Moon Phase",
        year=request_body.year,
        month=request_body.month,
        day=request_body.day,
        hour=request_body.hour,
        minute=request_body.minute,
        seconds=request_body.second,
        city="",
        nation="GB",
        lng=request_body.longitude,
        lat=request_body.latitude,
        tz_str=request_body.timezone,
        online=False,
        active_points=resolve_active_points(None),
        suppress_geonames_warning=True,
    )

    return MoonPhaseDetailsFactory.from_subject(
        subject,
        using_default_location=request_body.using_default_location,
        location_precision=request_body.location_precision,
    )


def _format_coordinate(value, precision: int) -> float:
    """Round a coordinate to the given number of decimal places."""
    rounded = round(float(value), precision)
    if rounded == 0.0:
        return 0.0
    return rounded


def moon_phase_payload(overview, *, omit_nulls: bool = False) -> dict:
    """Wrap a moon phase overview in a standard response payload."""
    data = dump(overview, omit_nulls=omit_nulls)

    location = data.get("location")
    if location:
        precision = location.get("precision", 0)
        location["latitude"] = _format_coordinate(location["latitude"], precision)
        location["longitude"] = _format_coordinate(location["longitude"], precision)

    return {
        "status": "OK",
        "moon_phase_overview": data,
    }


def moon_phase_context_payload(overview, *, omit_nulls: bool = False) -> dict:
    """Wrap a moon phase overview with AI-optimized context in a standard response payload."""
    data_payload = moon_phase_payload(overview, omit_nulls=omit_nulls)
    return {
        "status": data_payload["status"],
        "context": to_context(overview),
        "moon_phase_overview": data_payload["moon_phase_overview"],
    }
