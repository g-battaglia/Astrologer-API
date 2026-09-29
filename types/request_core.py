from __future__ import annotations

import inspect as _inspect
from abc import ABC
from logging import getLogger
from typing import TYPE_CHECKING, Any, Literal, Mapping, Optional, Union, get_args

from pydantic import BaseModel, Field, field_validator, model_validator
from zoneinfo import ZoneInfo, available_timezones

from kerykeion.schemas import KerykeionException
from kerykeion.utilities import localize_naive

import datetime


# ``Factory`` is a placeholder the tz database ships to stand in for "no zone
# configured yet". It loads, and it answers every question with offset 0, so
# accepting it would hand back a chart computed in UTC while the caller believes
# they named a place — a plausible-looking wrong answer, which is worse than a
# refusal. Dropping it also keeps the accepted set exactly what it was before
# this validator moved off its previous timezone library.
#
# Built once at import: available_timezones() rescans TZPATH and the tzdata
# package on every call (~1.9 ms measured here), and this predicate runs for
# every subject in a request — two or more on synastry and transit — so calling
# it per validation would put milliseconds of directory walking on the hot path.
# Membership in the frozen set is a few nanoseconds.
_VALID_TIMEZONES = frozenset(available_timezones()) - {"Factory"}


def _check_timezone(value: str) -> None:
    if value not in _VALID_TIMEZONES:
        raise ValueError(f"Invalid timezone '{value}'. Please use a valid timezone from the IANA database.")


def _check_date(year: int, month: int, day: int) -> None:
    y = year
    if y < 1:
        is_leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
        y = 4 if is_leap else 1
    try:
        datetime.date(y, month, day)
    except ValueError:
        raise ValueError(f"Invalid date: {year}-{month:02d}-{day:02d} does not exist.")


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    """Normalize an empty or whitespace-only string to ``None``.

    Return-search validators check ``iso_datetime is None`` to require a search
    anchor, while the handlers branch on its truthiness. A blank string slips
    past the ``is None`` check yet reads as falsy in the handler, so the request
    falls through to the year-based path with ``year=None`` and fails deep in
    the search routine. Collapsing blanks to ``None`` here keeps both views
    consistent: a blank ``iso_datetime`` is treated as "not provided".
    """
    if value is not None and not value.strip():
        return None
    return value


def _validate_iso_datetime(value: Optional[str]) -> None:
    """Reject a malformed ``iso_datetime`` at the request layer (→ 422).

    The return/helio/node handlers forward ``iso_datetime`` straight into
    kerykeion's ``*_from_iso_formatted_time`` methods, which call
    ``datetime.fromisoformat`` and raise a raw ``ValueError`` deep in the search
    routine — surfacing as an HTTP 500. Parsing it here turns a bad client value
    into a clean validation error. ``None``/blank is allowed (year-based path).
    """
    if value is None:
        return
    try:
        datetime.datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("iso_datetime must be a valid ISO-8601 datetime (e.g. '2025-05-01T00:00:00+00:00').")


def _parse_iso_range_naive_utc(start_date: str, end_date: str) -> "tuple[datetime.datetime, datetime.datetime]":
    """Parse a start/end ISO date(time) pair into naive-UTC datetimes.

    Raises ``ValueError`` (→ 422) on unparsable input or values outside the
    supported datetime range. Offset-aware inputs are normalized to naive UTC
    so the pair is always comparable.
    """
    try:
        start = datetime.datetime.fromisoformat(start_date)
        end = datetime.datetime.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError(f"start_date/end_date must be ISO dates: {exc}")
    try:
        if start.tzinfo is not None:
            start = start.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except OverflowError:
        raise ValueError("start_date/end_date is out of the supported range.")
    return start, end


def _count_ephemeris_samples(
    start_date: str,
    end_date: str,
    *,
    timezone_name: str,
    is_dst: bool | None,
    step_type: Literal["days", "hours", "minutes"],
    step: int,
) -> int:
    """Mirror ``EphemerisDataFactory`` sample sizing, including DST.

    Daily scans advance by local civil days. Sub-day scans localize the
    endpoints and advance by elapsed UTC time, so a fall-back fold adds an hour
    and a spring-forward gap removes one. Keeping this calculation identical
    at the request boundary prevents accepted requests from failing later with
    a factory resource-limit error.
    """
    try:
        start = datetime.datetime.fromisoformat(start_date)
        end = datetime.datetime.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError(f"start_date/end_date must be ISO dates: {exc}")

    local_timezone = ZoneInfo(timezone_name)

    def to_utc(value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            return localize_naive(value, local_timezone, is_dst=is_dst).astimezone(datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    try:
        start_utc = to_utc(start)
        end_utc = to_utc(end)
    except KerykeionException as exc:
        raise ValueError(
            "start_date/end_date contains an ambiguous or nonexistent local "
            "time in the requested timezone. Pass is_dst=true or is_dst=false "
            "to disambiguate it, or shift the timestamp outside the DST transition."
        ) from exc
    except OverflowError:
        raise ValueError("start_date/end_date is out of the supported range.")

    if end_utc <= start_utc:
        raise ValueError("end_date must be after start_date.")

    if step_type == "days":
        local_start = start if start.tzinfo is None else start.astimezone(local_timezone).replace(tzinfo=None)
        local_end = end if end.tzinfo is None else end.astimezone(local_timezone).replace(tzinfo=None)
        return (local_end - local_start).days // step + 1

    unit_seconds = 3600 if step_type == "hours" else 60
    elapsed_units = int((end_utc - start_utc).total_seconds() / unit_seconds)
    return elapsed_units // step + 1


from kerykeion.schemas import (
    ActiveAspect,
    AstrologicalPoint,
    HousesSystemIdentifier,
    KerykeionChartLanguage,
    KerykeionChartStyle,
    KerykeionChartTheme,
    KerykeionGlyphSize,
    PerspectiveType,
    SiderealMode,
    ZodiacType,
    CompositeChartType,
    CompositeHouseAnchor,
    DominantMethod,
)
from kerykeion.settings.config_constants import (
    ALL_ACTIVE_POINTS,
    DEFAULT_ACTIVE_ASPECTS,
    DEFAULT_ACTIVE_POINTS,
)
from kerykeion import PlanetaryReturnFactory
from kerykeion.aspects import orb_utils as _orb_utils
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy
from kerykeion.fixed_stars import FixedStarCatalog

from ..utils.rendering_validation import validate_colors_settings, validate_language_pack

if TYPE_CHECKING:
    ActivePointName = AstrologicalPoint
else:
    # Wire contract for `active_points`: the wheel points kerykeion v6 actually
    # accepts (ALL_ACTIVE_POINTS). `AstrologicalPoint` still carries 23
    # fixed-star literals for v5 compatibility, but `_normalize_active_points`
    # rejects them (stars belong in `subject.active_fixed_stars`), so the
    # published schema must not advertise them as valid values.
    ActivePointName = Literal.__getitem__(tuple(ALL_ACTIVE_POINTS))

logger = getLogger(__name__)

# Aspect-keyed per-point orb adjustments ({"Sun": {"*": 1.5, "conjunction": 3.0}})
# need engine support. Probed by capability, not by version string: the schema
# accepts the map form exactly when the engine underneath can honor it, so a
# payload sent through an older engine gets an honest 422 here instead of a
# ValueError deep inside the calculation (a 500 to the caller).
_ENGINE_SUPPORTS_ASPECT_KEYED_ORBS = hasattr(_orb_utils, "lookup_point_adjustment")

# The engine's own default for ``nakshatra_ayanamsa``. Declared here so the
# request models and ``router_utils`` agree on the single value that means
# "say nothing to the factory" — see ``_extract_v6_calculation_config``.
DEFAULT_NAKSHATRA_AYANAMSA: SiderealMode = "LAHIRI"

# ``AstrologicalSubjectFactory`` learned ``nakshatra_ayanamsa`` in a91;
# ``PlanetaryReturnFactory`` — which forwards the natal v6 flags to the return
# subject it builds — learned it separately. Probed the same way as the
# aspect-keyed orbs above, because the two are not guaranteed to land in the
# same release: the subject endpoints can honor the field while the twelve
# return endpoints (chart / chart-data / context × solar, lunar, node-crossing,
# heliocentric) would answer an unknown kwarg with a TypeError, i.e. a 500.
#
# Where the caller says nothing, the deploy-ahead rule keeps the kwarg off the
# call entirely and every engine works. Where the caller says something, the
# only two honest answers are "forward it" and "refuse"; silently dropping it
# is not among them, because the nakshatras would then come back read off
# uncorrected longitudes — wrong by nearly two mansions — with a response that
# claims the requested ayanamsa was used.
_ENGINE_RETURN_FACTORY_ACCEPTS_NAKSHATRA_AYANAMSA = "nakshatra_ayanamsa" in _inspect.signature(PlanetaryReturnFactory.__init__).parameters

PointOrbAdjustmentValue = Union[float, Mapping[str, float]]
"""A point's entry in `point_orb_adjustments`: a plain additive delta, or an
aspect-keyed mapping of aspect name -> delta with "*" as the default for
aspects not listed (`number` and `{"*": number}` are equivalent)."""


def _check_point_orb_adjustments_capability(
    value: Optional[Mapping[str, PointOrbAdjustmentValue]],
) -> Optional[Mapping[str, PointOrbAdjustmentValue]]:
    if value is None or _ENGINE_SUPPORTS_ASPECT_KEYED_ORBS:
        return value
    for point_name, adjustment in value.items():
        if isinstance(adjustment, Mapping):
            raise ValueError(
                f"point_orb_adjustments[{point_name!r}] is an aspect-keyed mapping, "
                "which the installed calculation engine does not support yet; "
                "pass a plain number per point."
            )
    return value

TIMING_MIN_YEAR = 1
TIMING_MAX_YEAR = 9999
MAX_ACTIVE_POINTS = 60

# Fixed stars requested on the ephemeris table are computed at every sample,
# exactly like active points, so they get their own dedicated request cap.
MAX_ACTIVE_FIXED_STARS = 60
# A computed star sample costs ~4x a point sample (measured 0.55 ms vs
# 0.126 ms per sample on the candidate stack): price stars honestly so the
# work-unit ceiling keeps bounding real CPU, not just element counts.
FIXED_STAR_WORK_UNIT_WEIGHT = 4

# Absolute upper bound shared by the broader scan endpoints. The dedicated
# ephemeris-table request has tighter sample/work budgets below because each
# sample materializes a complete subject and every requested point.
EPHEMERIS_MAX_POINTS = 20000
EPHEMERIS_MAX_SAMPLES = 732
EPHEMERIS_MAX_POINT_CALCULATIONS = 30000

# Points kerykeion's STANDARD_PLANETS table admits but whose "heliocentric
# return" is astronomically undefined: lunar-derived points oscillate around
# Earth's orbit rather than tracing their own heliocentric path (kerykeion
# itself only rejects Sun/Moon). Guarded app-side so the search cannot return
# a meaningless chart.
LUNAR_DERIVED_POINTS = frozenset(
    {
        "Mean_North_Lunar_Node",
        "True_North_Lunar_Node",
        "Mean_South_Lunar_Node",
        "True_South_Lunar_Node",
        "Mean_Lilith",
        "True_Lilith",
        "Interpolated_Lilith",
        "Mean_Priapus",
        "True_Priapus",
        "Interpolated_Perigee",
        "White_Moon",
    }
)

class StrictRequestModel(BaseModel):
    """Base for JSON request bodies with finite numeric inputs only."""

    model_config = {"extra": "forbid", "allow_inf_nan": False}


# ---------------------------------------------------------------------------
# Active Points Normalization
# ---------------------------------------------------------------------------
# Pre-computed lookup tables for case-insensitive point name normalization.
# Built once at module load for O(1) lookups per point.

_POINT_LOWER_TO_CANONICAL: dict[str, str] = {p.lower(): p for p in get_args(AstrologicalPoint)}

_POINT_ALIASES: dict[str, str] = {
    "mean_node": "Mean_North_Lunar_Node",
    "true_node": "True_North_Lunar_Node",
    "north_node": "Mean_North_Lunar_Node",
    "south_node": "Mean_South_Lunar_Node",
    "mean_south_node": "Mean_South_Lunar_Node",
    "true_south_node": "True_South_Lunar_Node",
    "mc": "Medium_Coeli",
    "ic": "Imum_Coeli",
    "asc": "Ascendant",
    "desc": "Descendant",
    "lilith": "Mean_Lilith",
    # Uranian / Hamburg School aliases
    "cupido_h": "Cupido",
    "hades_h": "Hades",
    "zeus_h": "Zeus",
    "kronos_h": "Kronos",
    "apollon_h": "Apollon",
    "admetos_h": "Admetos",
    "vulkanus_h": "Vulkanus",
    "poseidon_h": "Poseidon",
    # Lilith/Priapus aliases
    "interpolated_lilith": "Interpolated_Lilith",
    "mean_priapus": "Mean_Priapus",
    "true_priapus": "True_Priapus",
    # Arabic Parts aliases
    "part_of_fortune": "Pars_Fortunae",
    "lot_of_fortune": "Pars_Fortunae",
    "part_of_spirit": "Pars_Spiritus",
    "lot_of_spirit": "Pars_Spiritus",
}


def _normalize_point_name(name: str) -> str:
    """Normalize a point name to canonical format.

    Examples:
        'chiron' -> 'Chiron'
        'MERCURY' -> 'Mercury'
        'mean_node' -> 'Mean_North_Lunar_Node'
    """
    lower = name.lower()
    return _POINT_ALIASES.get(lower) or _POINT_LOWER_TO_CANONICAL.get(lower) or name


def _normalize_active_points(value: Optional[list]) -> Optional[list]:
    """Normalize and bound point names before any ephemeris work starts."""
    if value is None:
        return None
    if len(value) > MAX_ACTIVE_POINTS:
        raise ValueError(f"active_points accepts at most {MAX_ACTIVE_POINTS} entries.")
    if any(not isinstance(point, str) for point in value):
        raise ValueError("active_points entries must be strings.")

    normalized = [_normalize_point_name(point) for point in value]
    # AstrologicalPoint retains 23 fixed-star literals for v5 compatibility,
    # while Kerykeion v6 routes stars exclusively through active_fixed_stars.
    allowed = set(ALL_ACTIVE_POINTS)
    unknown = sorted({str(point) for point in normalized if point not in allowed})
    if unknown:
        preview = ", ".join(unknown[:5])
        suffix = " …" if len(unknown) > 5 else ""
        raise ValueError(f"Unknown active_points: {preview}{suffix}. Fixed stars belong in subject.active_fixed_stars.")
    if len(normalized) != len(set(normalized)):
        raise ValueError("active_points must not contain duplicate canonical points.")
    return normalized


def _normalize_active_fixed_stars(value: Optional[list]) -> Optional[list]:
    """Validate ephemeris fixed-star names before any ephemeris work starts.

    ``None`` and ``[]`` both mean "no stars" and normalize to ``None`` so the
    star-less request path stays byte-identical to the historical behavior.
    Names are checked against the same libephemeris catalog the subject
    endpoints resolve ``active_fixed_stars`` from (``FixedStarCatalog``).
    """
    if not value:
        return None
    if len(value) > MAX_ACTIVE_FIXED_STARS:
        raise ValueError(f"active_fixed_stars accepts at most {MAX_ACTIVE_FIXED_STARS} entries.")
    if any(not isinstance(star, str) for star in value):
        raise ValueError("active_fixed_stars entries must be strings.")
    unknown = sorted({star for star in value if not FixedStarCatalog.is_known_name(star)})
    if unknown:
        preview = ", ".join(unknown[:5])
        suffix = " …" if len(unknown) > 5 else ""
        raise ValueError(f"Unknown active_fixed_stars: {preview}{suffix}. Use GET /api/v6/fixed-stars/catalog to discover valid star names.")
    # Symmetry with active_points: canonicalize to the catalog name, then reject
    # duplicates. Without this, distinct spellings of one star (e.g. "Sirius" and
    # "sirius", or "Deneb Algedi" and "Deneb_Algedi") slip through and are each
    # counted against the ephemeris work budget, so a single star could weigh 2x.
    # Every entry resolved above via is_known_name, so find() never returns None.
    normalized = [FixedStarCatalog.find(star).name for star in value]  # type: ignore[union-attr]
    if len(normalized) != len(set(normalized)):
        raise ValueError("active_fixed_stars must not contain duplicate stars.")
    return normalized


# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

DistributionMethod = Literal["weighted", "pure_count"]


class AbstractBaseSubjectModel(StrictRequestModel, ABC):
    """Shared subject fields used across requests."""

    model_config = {"extra": "forbid"}

    year: int = Field(
        description=("Year component of the event in astronomical year numbering. Supports dates from 13200 BCE to 9999 CE. For BCE dates use: 0 = 1 BCE, -1 = 2 BCE, -2 = 3 BCE, etc."),
        ge=-13200,
        le=9999,
        examples=[1980, 0, -99],
    )
    month: int = Field(description="Month component of the event.", ge=1, le=12, examples=[12])
    day: int = Field(description="Day component of the event.", ge=1, le=31, examples=[12])
    hour: int = Field(description="Hour component of the event (0-23).", ge=0, le=23, examples=[12])
    minute: int = Field(description="Minute component of the event (0-59).", ge=0, le=59, examples=[12])
    second: Optional[int] = Field(
        default=0,
        description="Seconds component of the event (0-59).",
        ge=0,
        le=59,
        examples=[0],
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude of the location (-180 to 180).",
        ge=-180,
        le=180,
        examples=[0.0],
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude of the location (-90 to 90).",
        ge=-90,
        le=90,
        examples=[51.4825766],
    )
    altitude: Optional[float] = Field(
        default=None,
        description="Altitude above sea level in meters.",
        examples=[35.0],
    )
    city: str = Field(description="City name associated with the event.", examples=["London"])
    nation: Optional[str] = Field(
        default=None,
        description="Two-letter ISO 3166-1 alpha-2 nation code.",
        examples=["GB"],
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone identifier for the event.",
        examples=["Europe/London"],
    )
    is_dst: Optional[bool] = Field(
        default=None,
        description="Override automatic daylight saving time detection.",
    )
    geonames_username: Optional[str] = Field(
        default=None,
        description="Geonames username used to resolve location data when GPS coordinates are not provided.",
        examples=[None],
    )

    @field_validator("city")
    @classmethod
    def strip_city(cls, value: str) -> str:
        return value.strip()

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        _check_timezone(value)
        return value

    @field_validator("nation")
    @classmethod
    def validate_nation(cls, value: Optional[str]) -> str:
        if not value or value.lower() == "null":
            return "null"
        if len(value) != 2 or not value.isalpha():
            raise ValueError(f"Invalid nation code: '{value}'. It must be a 2-letter country code (ISO 3166-1 alpha-2).")
        return value.upper()

    @model_validator(mode="after")
    def validate_date(self) -> "AbstractBaseSubjectModel":
        _check_date(self.year, self.month, self.day)
        return self

    @model_validator(mode="after")
    def ensure_location_source(self) -> "AbstractBaseSubjectModel":
        lat = self.latitude
        lng = self.longitude
        tz = self.timezone
        geonames = self.geonames_username

        missing_coordinates = sum(field is None for field in (lat, lng, tz))

        if missing_coordinates == 3 and not geonames:
            raise ValueError("Provide latitude, longitude, timezone or specify geonames_username.")

        if 0 < missing_coordinates < 3 and not geonames:
            raise ValueError("Provide all location fields (latitude, longitude, timezone) or geonames_username.")

        # Complete explicit coordinates take priority over GeoNames (offline mode
        # is deterministic and avoids a network round trip); partial coordinates
        # are discarded in favour of the GeoNames lookup. Mirrors the behaviour
        # of ReturnLocationModel.
        if geonames:
            if missing_coordinates == 0:
                logger.info("Complete coordinates provided; ignoring the redundant GeoNames lookup.")
                self.geonames_username = None
            else:
                self.latitude = None
                self.longitude = None
                self.timezone = None

        return self


class SubjectModel(AbstractBaseSubjectModel):
    """Subject definition used across most endpoints."""

    model_config = {"extra": "forbid"}

    name: str = Field(default="Subject", description="Display name for the subject.", examples=["John Doe"])

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    zodiac_type: Optional[ZodiacType] = Field(
        default="Tropical",
        description="Zodiac type used for the calculation.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )
    perspective_type: Optional[PerspectiveType] = Field(
        default="Apparent Geocentric",
        description="Astronomical perspective used for the calculation.",
        examples=list(get_args(PerspectiveType)),
    )
    houses_system_identifier: Optional[HousesSystemIdentifier] = Field(
        default="P",
        description="Identifier for the house system.",
        examples=list(get_args(HousesSystemIdentifier)),
    )
    custom_ayanamsa_t0: Optional[float] = Field(
        default=None,
        description="Reference epoch as Julian Day for the USER sidereal mode. Required when sidereal_mode='USER'.",
        examples=[2451545.0],
    )
    custom_ayanamsa_ayan_t0: Optional[float] = Field(
        default=None,
        description="Ayanamsa offset in degrees at the reference epoch. Required when sidereal_mode='USER'.",
        examples=[23.5],
    )

    # --- v6 Calculation Configuration ---
    calculate_dignities: bool = Field(
        default=False,
        description="Compute essential dignities (domicile, exaltation, detriment, fall, peregrine) and Chaldean decans / Egyptian terms for each point.",
    )
    calculate_nakshatra: bool = Field(
        default=False,
        description="Compute Vedic Nakshatra (lunar mansion), pada, and Vimsottari Dasha lord for each point.",
    )
    nakshatra_ayanamsa: Optional[SiderealMode] = Field(
        default=DEFAULT_NAKSHATRA_AYANAMSA,
        description=(
            "Ayanamsa used to place the nakshatras on a non-sidereal chart. The nakshatras are a sidereal grid, "
            "so on a Tropical (or otherwise non-sidereal) chart their longitudes must be corrected by an ayanamsa "
            "before the mansion is read. Ignored when the chart is already Sidereal — there the chart's own "
            "`sidereal_mode` governs. Set to `null` for the uncorrected legacy values (tropical longitudes read "
            "straight onto the nakshatra grid). "
            "READING THE ECHO: `nakshatra_ayanamsa` and `nakshatra_ayanamsa_value` come back `null` in two "
            "different situations, told apart by `zodiac_type`. On a Sidereal chart they are `null` because the "
            "field was ignored — the chart's `sidereal_mode` already placed the grid, and the mansions are "
            "correct. On a Tropical chart they are `null` only when `null` was sent, and there it means the "
            "legacy uncorrected reading was used — every mansion, pada and dasha lord is offset by roughly two "
            "mansions. Same two nulls, opposite meanings."
        ),
        examples=[DEFAULT_NAKSHATRA_AYANAMSA],
    )
    calculate_gauquelin: bool = Field(
        default=False,
        description="Compute Gauquelin sector position (1-36) for each point.",
    )
    calculate_nutation: bool = Field(
        default=False,
        description="Compute nutation and obliquity parameters (true/mean obliquity, nutation in longitude/obliquity).",
    )
    calculate_local_space: bool = Field(
        default=False,
        description="Compute azimuth and altitude above horizon for each point from the observer's location.",
    )
    active_fixed_stars: Optional[list[str]] = Field(
        default=None,
        description="Fixed star names to compute from the libephemeris catalog (no automatic defaults, max 60, no duplicates). Use `GET /api/v6/fixed-stars/catalog` to discover available names; an unknown name is a 422.",
        examples=[["Rigel", "Sirius", "Vega", "Vindemiatrix"]],
    )

    @field_validator("active_fixed_stars")
    @classmethod
    def _validate_active_fixed_stars(cls, value: Optional[list]) -> Optional[list]:
        # Same contract as /advanced/ephemeris: cap, catalog membership and
        # duplicates are rejected up front instead of being silently dropped.
        return _normalize_active_fixed_stars(value)
    active_midpoints: Optional[list[str]] = Field(
        default=None,
        description=(
            "Midpoint pair identifiers (`'<name_a>_<name_b>'`) to materialize as sensitive points on the chart wheel. "
            "Format mirrors the natal point names, e.g. `'Sun_Moon'`, `'Sun_Mercury'`, `'Sun_True_North_Lunar_Node'`. "
            "Unknown pairs are silently skipped."
        ),
        examples=[["Sun_Moon", "Sun_Mercury"]],
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_zodiac_and_sidereal(self) -> "SubjectModel":
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")
        if self.sidereal_mode == "USER":
            if self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None:
                raise ValueError("custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are required when sidereal_mode='USER'.")
        return self

    @field_validator("perspective_type", mode="before")
    @classmethod
    def default_perspective_type(cls, value: Optional[PerspectiveType]) -> PerspectiveType:
        return value or "Apparent Geocentric"

    @field_validator("houses_system_identifier", mode="before")
    @classmethod
    def default_house_system(cls, value: Optional[HousesSystemIdentifier]) -> HousesSystemIdentifier:
        return value or "P"


class TransitSubjectModel(AbstractBaseSubjectModel):
    """Transit subject definition; inherits base validators."""

    model_config = {"extra": "ignore"}

    name: Optional[str] = Field(default="Transit", description="Label used for the transit subject.")


class ChartDataConfigurationMixin(StrictRequestModel):
    """Mixin holding computation options for chart data (no rendering)."""

    model_config = {"extra": "forbid"}

    active_points: Optional[list[Union[ActivePointName, str]]] = Field(
        default=None,
        description="Override the active points used for calculations.",
        examples=[DEFAULT_ACTIVE_POINTS],
    )
    active_aspects: Optional[list[ActiveAspect]] = Field(
        default=None,
        description="Override the active aspects and their orbs.",
        examples=[DEFAULT_ACTIVE_ASPECTS],
    )
    distribution_method: DistributionMethod = Field(
        default="weighted",
        description="Element/quality distribution strategy.",
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Normalize point names to canonical format, accepting case-insensitive and aliased inputs."""
        return _normalize_active_points(value)

    custom_distribution_weights: Optional[Mapping[str, float]] = Field(
        default=None,
        description="Custom weights used when distribution_method='weighted'.",
        examples=[
            {
                "sun": 2.0,
                "moon": 2.0,
                "ascendant": 2.0,
                "medium_coeli": 1.5,
                "mercury": 1.5,
                "venus": 1.5,
                "mars": 1.5,
                "jupiter": 1.0,
                "saturn": 1.0,
            }
        ],
    )
    axis_orb_limit: Optional[float] = Field(
        default=None,
        description="Override the maximum orb (in degrees) for aspects involving axial points (ASC, MC, DSC, IC). When set, axial aspects use this orb instead of the default per-aspect orb.",
        ge=0,
        le=30,
    )
    point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustmentValue]] = Field(
        default=None,
        description="Per-point orb adjustment table (point name → degrees added to the aspect base orb "
        "when that point is involved). When omitted, the chart-type default applies — natal/synastry "
        "use a +1.5° luminary bonus (Sun, Moon), predictive charts use no adjustment. Pass an empty "
        "object to disable the default. An entry can also vary by aspect: an object of aspect name → "
        "degrees with '*' as the default for aspects not listed ({\"Sun\": {\"*\": 1.5, \"conjunction\": 3.0}} "
        "applies 3.0° to Sun conjunctions and 1.5° to every other Sun aspect; without '*' the point is "
        "unconfigured for unlisted aspects). A number and {\"*\": number} are equivalent.",
        examples=[{"Sun": 1.5, "Moon": 1.5}, {"Sun": {"*": 1.5, "conjunction": 3.0}, "Ascendant": {"conjunction": -3.0}}],
    )

    @field_validator("point_orb_adjustments")
    @classmethod
    def _check_point_orb_capability(cls, value):
        return _check_point_orb_adjustments_capability(value)
    point_orb_adjustment_strategy: OrbAdjustmentStrategy = Field(
        default="max_explicit",
        description="How to combine the two points' orb adjustments: 'max_explicit' (widest configured adjustment wins — the classic luminary rule), 'min_explicit', 'sum', or 'none' (disabled).",
    )


class ChartRenderingMixin(ChartDataConfigurationMixin):
    """Mixin adding chart rendering options (theme, language, split_chart, transparent background, runtime ChartDrawer tweaks)."""

    model_config = {"extra": "forbid"}

    theme: Optional[KerykeionChartTheme] = Field(
        default="classic",
        description="Visual theme for the generated SVG chart.",
        examples=list(get_args(KerykeionChartTheme)),
    )
    language: Optional[KerykeionChartLanguage] = Field(
        default="EN",
        description="Language used for chart labels.",
        examples=list(get_args(KerykeionChartLanguage)),
    )
    split_chart: bool = Field(
        default=False,
        description="Return wheel and aspect grid as separate SVG strings in 'chart_wheel' and 'chart_grid' keys.",
    )
    transparent_background: bool = Field(
        default=False,
        description="Render chart with transparent background instead of theme default.",
    )
    show_house_position_comparison: bool = Field(
        default=True,
        description="Display the house comparison table next to the chart wheel.",
    )
    show_cusp_position_comparison: bool = Field(
        default=True,
        description="Display the cusp position comparison table next to the chart wheel (for dual charts).",
    )
    show_degree_indicators: bool = Field(
        default=True,
        description="Display radial lines and degree numbers for planet positions on the chart wheel.",
    )
    show_aspect_icons: bool = Field(
        default=True,
        description="Display aspect icons on the chart wheel aspect lines.",
    )
    custom_title: Optional[str] = Field(
        default=None,
        description="Temporarily override the rendered chart title (max 40 characters).",
        max_length=40,
        examples=["Custom Chart Title"],
    )
    style: KerykeionChartStyle = Field(
        default="classic",
        description="Chart rendering style: 'classic' (traditional wheel) or 'modern' (concentric rings).",
        examples=list(get_args(KerykeionChartStyle)),
    )
    glyph_size: KerykeionGlyphSize = Field(
        default="medium",
        description=(
            "Size of the planet cluster on the wheel: 'small', 'medium' (default) or 'large' "
            "(the planet glyph at the classic style's own size, "
            "in the default configuration — zodiac background ring active). "
            "Only affects 'modern' style \u2014 the classic wheel draws a fixed-size glyph."
        ),
        examples=list(get_args(KerykeionGlyphSize)),
    )
    show_zodiac_background_ring: bool = Field(
        default=True,
        description="Show colored zodiac sign wedges on the wheel. Only affects 'modern' style.",
    )
    show_diurnality: bool = Field(
        default=True,
        description=(
            "Print the chart's diurnality (whether the Sun stood above or below the horizon) "
            "in the bottom-left info panel, e.g. 'Diurnality: Nocturnal'. Dual charts report both "
            "wheels and use no heading, e.g. 'Natal Nocturnal \u00b7 Transit Diurnal' (synastry names "
            "the two subjects, truncated). Set to false to omit the line and reclaim its space. "
            "No effect where the line is never drawn: on wheel-only output (split_chart=true), "
            "on midpoint composites, and on charts whose *subject* is heliocentric \u2014 which draw "
            "outward from the Sun, so the Sun is not among their points and there is nothing for "
            "the line to describe; a midpoint composite represents no single sky. "
            "The endpoint named /chart/heliocentric-return is not automatically such a chart: "
            "'heliocentric' there describes how the return instant is found, and the chart is drawn in "
            "whatever perspective the subject carries \u2014 Apparent Geocentric by default, in which case "
            "the line is drawn; a heliocentric subject makes the return heliocentric too, and it is not."
        ),
    )
    show_motion_state: bool = Field(
        default=False,
        description=(
            "Mark stationary planets on the wheel. A planet caught at a station is labelled next to "
            "its glyph — 'SR' when it is turning retrograde, 'SD' when it is turning direct — so a "
            "chart cast within a day or two of a station shows it instead of leaving the reader to "
            "compare speeds. Planets in ordinary direct or retrograde motion are left unmarked, and "
            "a chart with no station renders unchanged. The same classification is in the JSON as "
            "each point's 'motion_state'."
        ),
    )
    show_out_of_bounds: bool = Field(
        default=False,
        description=(
            "Badge out-of-bounds points with 'OOB' in the point tables beside the wheel. A point is "
            "out of bounds when its declination lies beyond the Sun's own extremes (about ±23°26'), "
            "which the Moon and the inner planets reach regularly. Marks the tables only; the wheel "
            "glyphs are untouched. Points whose declination is not computed carry no badge."
        ),
    )
    show_aspect_movement: bool = Field(
        default=False,
        description=(
            "Draw separating aspects with a dashed line and applying aspects solid, so the direction "
            "of an aspect is readable off the wheel instead of only from the JSON. Affects the aspect "
            "lines inside the wheel; the aspect grid and the aspect list are unchanged."
        ),
    )
    show_relationship_score: bool = Field(
        default=False,
        description=(
            "Print the synastry relationship score in the bottom-left info panel. The line is drawn "
            "only where a score exists: a synastry chart computed with 'include_relationship_score' "
            "left at its default true. Turning this on does not compute the score — it prints the one "
            "already in the response — so on any other chart type, or with "
            "'include_relationship_score' set to false, it has no effect."
        ),
    )
    show_ayanamsa_value: bool = Field(
        default=False,
        description=(
            "Append the ayanamsa offset in degrees to the zodiac line of the info panel, e.g. "
            "'Sidereal LAHIRI (24°11')' instead of 'Sidereal LAHIRI'. Sidereal charts only — a "
            "tropical chart has no ayanamsa and renders unchanged. The same value is in the JSON as "
            "the subject's 'ayanamsa_value'."
        ),
    )
    show_polar_fallback_note: bool = Field(
        default=False,
        description=(
            "Mark the house-system line of the info panel when the requested system could not be "
            "used. Several house systems are undefined above the polar circles and the engine "
            "substitutes one that is defined there; without this flag the chart names the system "
            "actually drawn and says nothing about the substitution, which reads as if the request "
            "had been honoured. No effect on charts where no substitution happened."
        ),
    )
    double_chart_aspect_grid_type: Literal["list", "table"] = Field(
        default="list",
        description="Layout for double-chart aspect display: 'list' (vertical) or 'table' (grid matrix).",
    )
    # --- v6 Advanced Rendering Options ---
    external_view: bool = Field(
        default=False,
        description="Render the 'ExternalNatal' layout, placing planet glyphs on the outside of the wheel.",
    )
    auto_size: bool = Field(
        default=True,
        description="Automatically size the SVG to fit the chart content.",
    )
    padding: int = Field(
        default=20,
        description="Padding around the chart in pixels.",
        ge=0,
        le=100,
    )
    colors_settings: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Override documented chart color keys with plain CSS colors only: hex, named, "
            "rgb()/rgba()/hsl()/hsla(), or var(--name) without a fallback. Unknown keys, "
            "url(), markup and arbitrary CSS are rejected."
        ),
    )
    language_pack: Optional[dict[str, str]] = Field(
        default=None,
        description="Custom language pack overriding chart label translations.",
    )

    @field_validator("colors_settings")
    @classmethod
    def validate_chart_colors(cls, value: Optional[dict[str, str]]) -> Optional[dict[str, str]]:
        return validate_colors_settings(value)

    @field_validator("language_pack")
    @classmethod
    def validate_custom_language_pack(cls, value: Optional[dict[str, str]]) -> Optional[dict[str, str]]:
        return validate_language_pack(value)

    @field_validator("custom_title")
    @classmethod
    def normalize_custom_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class BirthChartRequestModel(ChartRenderingMixin):
    """Request payload for the birth chart endpoint (with SVG rendering)."""

    subject: SubjectModel = Field(description="Subject used for the birth chart calculation.")


class BirthChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the birth chart data endpoint (data only, no SVG).

    Supports two modes:

    - **Compute mode** (default): provide ``subject`` to calculate the chart from scratch.
    - **Pre-computed mode**: provide ``chart_data`` (as returned by any ``/chart/*`` or
      ``/context/*`` endpoint) to skip calculation and generate the AI context directly.
    """

    subject: Optional[SubjectModel] = Field(
        default=None,
        description="Subject used for the birth chart calculation. Required when chart_data is not provided.",
    )
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-computed chart data object as returned by /chart/* or /context/* endpoints. "
            "When provided, the endpoint skips chart calculation and generates the AI context "
            "directly from this data. Mutually exclusive with subject."
        ),
    )

    @model_validator(mode="after")
    def require_subject_or_chart_data(self) -> "BirthChartDataRequestModel":
        if self.subject is None and self.chart_data is None:
            raise ValueError("Provide either 'subject' (to compute from scratch) or 'chart_data' (pre-computed).")
        return self


class SynastryChartRequestModel(ChartRenderingMixin):
    """Request payload for the synastry chart endpoint (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Primary subject (inner wheel).")
    second_subject: SubjectModel = Field(description="Secondary subject (outer wheel).")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )
    include_relationship_score: bool = Field(
        default=True,
        description=(
            "Include relationship score analysis in the computed data. This is the JSON figure; "
            "printing it on the SVG is a separate switch, 'show_relationship_score', which draws the "
            "line only when this one computed a score."
        ),
    )


class SynastryChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the synastry chart data endpoint (data only, no SVG).

    Supports two modes:

    - **Compute mode**: provide ``first_subject`` and ``second_subject``.
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    first_subject: Optional[SubjectModel] = Field(default=None, description="Primary subject (inner wheel).")
    second_subject: Optional[SubjectModel] = Field(default=None, description="Secondary subject (outer wheel).")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )
    include_relationship_score: bool = Field(
        default=True,
        description="Include relationship score analysis in the computed data.",
    )
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-computed chart data object as returned by /chart/* or /context/* endpoints. When provided, the endpoint skips chart calculation and generates the AI context directly from this data."
        ),
    )

    @model_validator(mode="after")
    def require_subjects_or_chart_data(self) -> "SynastryChartDataRequestModel":
        if self.chart_data is None and (self.first_subject is None or self.second_subject is None):
            raise ValueError("Provide either 'chart_data' (pre-computed) or both 'first_subject' and 'second_subject'.")
        return self


class TransitChartRequestModel(ChartRenderingMixin):
    """Request payload for the transit chart endpoint (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Natal subject used for the transit calculation.")
    transit_subject: TransitSubjectModel = Field(description="Transit moment data.")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )


class TransitChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for the transit chart data endpoint (data only, no SVG).

    Supports two modes:

    - **Compute mode**: provide ``first_subject`` and ``transit_subject``.
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    first_subject: Optional[SubjectModel] = Field(default=None, description="Natal subject used for the transit calculation.")
    transit_subject: Optional[TransitSubjectModel] = Field(default=None, description="Transit moment data.")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in the computed data.",
    )
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-computed chart data object as returned by /chart/* or /context/* endpoints. When provided, the endpoint skips chart calculation and generates the AI context directly from this data."
        ),
    )

    @model_validator(mode="after")
    def require_subjects_or_chart_data(self) -> "TransitChartDataRequestModel":
        if self.chart_data is None and (self.first_subject is None or self.transit_subject is None):
            raise ValueError("Provide either 'chart_data' (pre-computed) or both 'first_subject' and 'transit_subject'.")
        return self


class TransitBatchLocationModel(StrictRequestModel):
    """Location-only override for the transit ring of a batch scan.

    Only the geographic fields are read by the batch handler; a full transit
    subject (with date/time fields) is still accepted and its extra fields
    are ignored.
    """

    model_config = {"extra": "ignore"}

    city: Optional[str] = Field(default=None, description="City name for the transit location.")
    nation: Optional[str] = Field(default=None, description="ISO country code for the transit location.")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Latitude of the transit location.")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Longitude of the transit location.")
    timezone: Optional[str] = Field(default=None, description="IANA timezone of the transit location.")

    @model_validator(mode="after")
    def require_complete_coordinates(self) -> "TransitBatchLocationModel":
        # The handler applies each field independently over the natal
        # location; a partial coordinate set would silently mix an override
        # latitude with the natal longitude/timezone and produce a
        # plausibly-wrong transit ring.
        coords = (self.latitude, self.longitude, self.timezone)
        if any(c is not None for c in coords) and not all(c is not None for c in coords):
            raise ValueError("Provide latitude, longitude and timezone together (or none of them) in 'location'.")
        return self


class TransitBatchRequestModel(ChartDataConfigurationMixin):
    """Request payload for batch transit chart data (N dates, single request)."""

    first_subject: SubjectModel = Field(description="Natal subject.")
    start_date: str = Field(description="ISO date string for start of range, e.g. '2026-04-01'.")
    end_date: str = Field(description="ISO date string for end of range, e.g. '2026-04-30'.")
    step_days: int = Field(default=1, ge=1, le=30, description="Day step between transit dates.")
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison in each transit.",
    )
    location: Optional[TransitBatchLocationModel] = Field(
        default=None,
        description="Override transit location. If omitted, uses natal subject location.",
    )

    @model_validator(mode="after")
    def validate_range(self) -> "TransitBatchRequestModel":
        start, end = _parse_iso_range_naive_utc(self.start_date, self.end_date)
        if end < start:
            raise ValueError("end_date must be on or after start_date.")
        # Each step is a full transit-chart computation; cap the total work.
        steps = (end - start).days // self.step_days + 1
        if steps > 366:
            raise ValueError(f"Range too large: {steps} transit computations requested (max 366). Reduce the date span or increase step_days.")
        return self


class NowSubjectDefinitionModel(StrictRequestModel):
    """Configuration for the 'now' subject (name, zodiac, etc.)."""

    model_config = {"extra": "forbid"}

    name: str = Field(default="Now", description="Display name for the subject.")
    zodiac_type: Optional[ZodiacType] = Field(
        default="Tropical",
        description="Zodiac type used for the calculation.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )
    perspective_type: Optional[PerspectiveType] = Field(
        default="Apparent Geocentric",
        description="Astronomical perspective used for the calculation.",
        examples=list(get_args(PerspectiveType)),
    )
    houses_system_identifier: Optional[HousesSystemIdentifier] = Field(
        default="P",
        description="Identifier for the house system.",
        examples=list(get_args(HousesSystemIdentifier)),
    )
    custom_ayanamsa_t0: Optional[float] = Field(
        default=None,
        description="Reference epoch as Julian Day for the USER sidereal mode. Required when sidereal_mode='USER'.",
        examples=[2451545.0],
    )
    custom_ayanamsa_ayan_t0: Optional[float] = Field(
        default=None,
        description="Ayanamsa offset in degrees at the reference epoch. Required when sidereal_mode='USER'.",
        examples=[23.5],
    )

    # --- v6 Calculation Configuration ---
    calculate_dignities: bool = Field(default=False, description="Compute essential dignities for each point.")
    calculate_nakshatra: bool = Field(default=False, description="Compute Vedic Nakshatra for each point.")
    nakshatra_ayanamsa: Optional[SiderealMode] = Field(
        default=DEFAULT_NAKSHATRA_AYANAMSA,
        description=(
            "Ayanamsa used to place the nakshatras on a non-sidereal chart; ignored when the chart is already "
            "Sidereal. `null` returns the uncorrected legacy values. The echoed `nakshatra_ayanamsa` / "
            "`nakshatra_ayanamsa_value` are `null` both when the field was ignored (Sidereal chart, mansions "
            "correct) and when `null` was sent (Tropical chart, mansions uncorrected); `zodiac_type` tells the "
            "two apart."
        ),
        examples=[DEFAULT_NAKSHATRA_AYANAMSA],
    )
    calculate_gauquelin: bool = Field(default=False, description="Compute Gauquelin sector positions.")
    calculate_nutation: bool = Field(default=False, description="Compute nutation and obliquity parameters.")
    calculate_local_space: bool = Field(default=False, description="Compute azimuth and altitude for each point.")
    active_fixed_stars: Optional[list[str]] = Field(default=None, description="Fixed star names to compute from the libephemeris catalog (no automatic defaults, max 60, no duplicates; an unknown name is a 422).")

    @field_validator("active_fixed_stars")
    @classmethod
    def _validate_active_fixed_stars(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_fixed_stars(value)
    active_midpoints: Optional[list[str]] = Field(
        default=None,
        description=(
            "Midpoint pair identifiers (`'<name_a>_<name_b>'`) to materialize as sensitive points on the chart wheel. Format mirrors the natal point names, e.g. `'Sun_Moon'`, `'Sun_Mercury'`."
        ),
        examples=[["Sun_Moon", "Sun_Mercury"]],
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_zodiac_configuration(self) -> "NowSubjectDefinitionModel":
        zodiac_type = self.zodiac_type
        sidereal_mode = self.sidereal_mode

        if sidereal_mode and zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")

        if zodiac_type == "Sidereal" and not sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")

        if sidereal_mode == "USER" and (self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None):
            raise ValueError("custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are required when sidereal_mode='USER'.")

        return self

    @field_validator("perspective_type", mode="before")
    @classmethod
    def default_perspective_type(cls, value: Optional[PerspectiveType]) -> PerspectiveType:
        return value or "Apparent Geocentric"

    @field_validator("houses_system_identifier", mode="before")
    @classmethod
    def default_house_system(cls, value: Optional[HousesSystemIdentifier]) -> HousesSystemIdentifier:
        return value or "P"


class NowChartRequestModel(NowSubjectDefinitionModel, ChartRenderingMixin):
    """Request payload for the 'now' chart endpoint (with SVG rendering)."""

    pass


class NowSubjectRequestModel(NowSubjectDefinitionModel):
    """Request payload for the 'now' subject endpoint."""

    active_points: Optional[list[Union[ActivePointName, str]]] = Field(
        default=None,
        description="Override the active points used for calculations.",
        examples=[DEFAULT_ACTIVE_POINTS],
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        return _normalize_active_points(value)


class BirthDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for retrieving subject data without charts."""

    subject: SubjectModel = Field(description="Subject used for the birth data calculation.")


class CompositeChartRequestModel(ChartRenderingMixin):
    """Request payload for composite chart calculations (with SVG rendering)."""

    first_subject: SubjectModel = Field(description="Primary subject used for the composite chart.")
    second_subject: SubjectModel = Field(description="Secondary subject used for the composite chart.")
    composite_type: CompositeChartType = Field(
        default="Midpoint",
        description="Composite calculation method: 'Midpoint' (classical midpoint) or 'Davison' (time-space midpoint).",
    )
    house_anchor: CompositeHouseAnchor = Field(
        default="auto",
        description=(
            "Which composite angle keeps its near midpoint when the two charts' houses admit a common frame: 'auto' (the default), 'ascendant' or 'midheaven'. Midpoint composites record the request in 'house_anchor' and what became of it in 'house_frame'; a Davison chart is cast as an ordinary chart and ignores it."
        ),
    )


class CompositeChartDataRequestModel(ChartDataConfigurationMixin):
    """Request payload for composite chart data calculations (data only, no SVG).

    Supports two modes:

    - **Compute mode**: provide ``first_subject`` and ``second_subject``.
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    first_subject: Optional[SubjectModel] = Field(default=None, description="Primary subject used for the composite chart.")
    second_subject: Optional[SubjectModel] = Field(default=None, description="Secondary subject used for the composite chart.")
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-computed chart data object as returned by /chart/* or /context/* endpoints. When provided, the endpoint skips chart calculation and generates the AI context directly from this data."
        ),
    )

    @model_validator(mode="after")
    def require_subjects_or_chart_data(self) -> "CompositeChartDataRequestModel":
        if self.chart_data is None and (self.first_subject is None or self.second_subject is None):
            raise ValueError("Provide either 'chart_data' (pre-computed) or both 'first_subject' and 'second_subject'.")
        return self

    composite_type: CompositeChartType = Field(
        default="Midpoint",
        description="Composite calculation method: 'Midpoint' (classical midpoint) or 'Davison' (time-space midpoint).",
    )
    house_anchor: CompositeHouseAnchor = Field(
        default="auto",
        description=(
            "Which composite angle keeps its near midpoint when the two charts' houses admit a common frame: 'auto' (the default), 'ascendant' or 'midheaven'. Midpoint composites record the request in 'house_anchor' and what became of it in 'house_frame'; a Davison chart is cast as an ordinary chart and ignores it."
        ),
    )


class ReturnLocationModel(StrictRequestModel):
    """Optional location override for planetary return calculations."""

    model_config = {"extra": "forbid"}

    city: Optional[str] = Field(default=None, description="Target city for the return chart.")
    nation: Optional[str] = Field(
        default=None,
        description="Two-letter ISO nation code.",
        examples=["GB"],
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude of the target location.",
        ge=-180,
        le=180,
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude of the target location.",
        ge=-90,
        le=90,
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Timezone of the target location.",
        examples=["Europe/London"],
    )
    altitude: Optional[float] = Field(
        default=None,
        description="Altitude in meters for the target location.",
    )
    geonames_username: Optional[str] = Field(
        default=None,
        description="Geonames username to resolve the provided city when coordinates are missing.",
    )

    @field_validator("city")
    @classmethod
    def strip_city(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        _check_timezone(value)
        return value

    @field_validator("nation")
    @classmethod
    def validate_nation(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value) != 2 or not value.isalpha():
            raise ValueError(f"Invalid nation code: '{value}'. It must be a 2-letter country code (ISO 3166-1 alpha-2).")
        return value.upper()

    @model_validator(mode="after")
    def ensure_location_source(self) -> "ReturnLocationModel":
        lat = self.latitude
        lng = self.longitude
        tz = self.timezone
        geonames = self.geonames_username

        missing_coordinates = sum(field is None for field in (lat, lng, tz))

        if missing_coordinates == 3 and not geonames and not (self.city and self.nation):
            raise ValueError("Provide latitude, longitude, timezone, or supply geonames_username with city and nation.")

        if 0 < missing_coordinates < 3 and not geonames:
            raise ValueError("Provide all location fields (latitude, longitude, timezone) or geonames_username.")

        # If complete coordinates are provided, they take priority; clear geonames_username
        if missing_coordinates == 0 and geonames:
            logger.info("Complete return coordinates provided; ignoring the redundant GeoNames lookup.")
            self.geonames_username = None

        return self


class PlanetaryReturnRequestModel(ChartRenderingMixin):
    """Shared payload for solar and lunar return endpoints (with SVG rendering)."""

    subject: SubjectModel = Field(description="Natal subject used for the return calculation.")
    year: Optional[int] = Field(
        default=None,
        description=("Year to search for the next return (astronomical numbering: 0 = 1 BCE, -1 = 2 BCE, etc.). Supports range -13200 to 9999."),
        ge=-13200,
        le=9999,
    )
    month: Optional[int] = Field(
        default=None,
        description="Optional month (1-12) to start the search from. Used with year and day.",
        ge=1,
        le=12,
    )
    day: Optional[int] = Field(
        default=1,
        description="Optional day (1-31) to start the search from. Requires month and year.",
        ge=1,
        le=31,
    )
    iso_datetime: Optional[str] = Field(
        default=None,
        description="ISO formatted datetime used as starting point for the search.",
        examples=["2025-05-01T00:00:00+00:00"],
    )
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction from the starting point. 'next' finds the upcoming return (default); 'previous' finds the most recent past return. Seeded with the instant of a return this API reported, 'next' yields the following return and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution return instants are reported at. Requires the libephemeris backend for backward search."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(
        default="dual",
        description="Return chart configuration: 'dual' wheel (natal + return) or 'single' wheel.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison for dual wheel returns.",
    )
    return_location: Optional[ReturnLocationModel] = Field(
        default=None,
        description="Override location used for the return chart.",
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "PlanetaryReturnRequestModel":
        # NOTE: explicit `is None` checks — year=0 (1 BCE) is falsy but valid.
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year' (with optional month and day) to locate the return.")

        if self.month is not None and self.year is None:
            raise ValueError("Month can only be provided together with a year.")

        if self.day is not None and self.day != 1 and self.month is None:
            raise ValueError("Day can only be provided together with month and year.")

        if self.year is not None and self.month is not None:
            _check_date(self.year, self.month, self.day or 1)

        if self.wheel_type == "single":
            self.include_house_comparison = False

        return self


class MoonPhaseRequestModel(StrictRequestModel):
    """Request payload for moon phase details at a specific date/time and location."""

    model_config = {"extra": "forbid"}

    year: int = Field(description="Year of the event (astronomical numbering: 0 = 1 BCE, -1 = 2 BCE).", ge=-13200, le=9999, examples=[1993])
    month: int = Field(description="Month of the event.", ge=1, le=12, examples=[10])
    day: int = Field(description="Day of the event.", ge=1, le=31, examples=[10])
    hour: int = Field(description="Hour of the event (0-23).", ge=0, le=23, examples=[12])
    minute: int = Field(description="Minute of the event (0-59).", ge=0, le=59, examples=[12])
    second: int = Field(
        default=0,
        description="Seconds of the event (0-59).",
        ge=0,
        le=59,
        examples=[0],
    )
    latitude: float = Field(
        description="Latitude of the location (-90 to 90).",
        ge=-90,
        le=90,
        examples=[51.5074],
    )
    longitude: float = Field(
        description="Longitude of the location (-180 to 180).",
        ge=-180,
        le=180,
        examples=[-0.1276],
    )
    timezone: str = Field(
        description="IANA timezone identifier for the event.",
        examples=["Europe/London"],
    )
    using_default_location: bool = Field(
        default=False,
        description="Flag indicating whether the location is a default fallback.",
    )
    location_precision: int = Field(
        default=0,
        description="Number of decimal places used to round latitude and longitude in the response.",
        ge=0,
        le=10,
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_date(self) -> "MoonPhaseRequestModel":
        _check_date(self.year, self.month, self.day)
        return self


class SunTimesRequestModel(StrictRequestModel):
    """Request payload for sunrise / sunset / solar-noon for a date + location."""

    model_config = {"extra": "forbid"}

    year: int = Field(description="Civil year (1-9999 CE).", ge=TIMING_MIN_YEAR, le=TIMING_MAX_YEAR, examples=[2026])
    month: int = Field(description="Month.", ge=1, le=12, examples=[5])
    day: int = Field(description="Day.", ge=1, le=31, examples=[28])
    latitude: float = Field(description="Latitude (-90 to 90).", ge=-90, le=90, examples=[41.9028])
    longitude: float = Field(description="Longitude (-180 to 180).", ge=-180, le=180, examples=[12.4964])
    timezone: str = Field(description="IANA timezone identifier.", examples=["Europe/Rome"])

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_date(self) -> "SunTimesRequestModel":
        _check_date(self.year, self.month, self.day)
        return self


class PlanetaryHoursRequestModel(StrictRequestModel):
    """Request payload for planetary (Chaldean) hour rulers at a moment + location."""

    model_config = {"extra": "forbid"}

    year: int = Field(
        description="Civil year (1-9999 CE); boundary dates must allow an adjacent civil day.",
        ge=TIMING_MIN_YEAR,
        le=TIMING_MAX_YEAR,
        examples=[2026],
    )
    month: int = Field(description="Month.", ge=1, le=12, examples=[5])
    day: int = Field(description="Day.", ge=1, le=31, examples=[28])
    hour: int = Field(description="Hour (0-23).", ge=0, le=23, examples=[11])
    minute: int = Field(default=0, description="Minute (0-59).", ge=0, le=59, examples=[30])
    latitude: float = Field(description="Latitude (-90 to 90).", ge=-90, le=90, examples=[41.9028])
    longitude: float = Field(description="Longitude (-180 to 180).", ge=-180, le=180, examples=[12.4964])
    timezone: str = Field(description="IANA timezone identifier.", examples=["Europe/Rome"])

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_date(self) -> "PlanetaryHoursRequestModel":
        _check_date(self.year, self.month, self.day)
        if (self.year, self.month, self.day) in (
            (TIMING_MIN_YEAR, 1, 1),
            (TIMING_MAX_YEAR, 12, 31),
        ):
            raise ValueError("Planetary hours require an adjacent civil day within years 1-9999.")
        return self


class MoonVocRequestModel(StrictRequestModel):
    """Request payload for void-of-course Moon at a moment.

    Void-of-course depends only on geocentric ecliptic longitudes, so it is
    independent of the observer's location — no latitude/longitude are needed. The
    timezone interprets the input clock time and localises the returned window.
    Both the tropical and sidereal zodiacs are supported.
    """

    model_config = {"extra": "forbid"}

    year: int = Field(description="Year (1-9999 CE).", ge=TIMING_MIN_YEAR, le=TIMING_MAX_YEAR, examples=[2026])
    month: int = Field(description="Month.", ge=1, le=12, examples=[6])
    day: int = Field(description="Day.", ge=1, le=31, examples=[1])
    hour: int = Field(description="Hour (0-23).", ge=0, le=23, examples=[9])
    minute: int = Field(default=0, description="Minute (0-59).", ge=0, le=59, examples=[0])
    timezone: str = Field(description="IANA timezone identifier.", examples=["Europe/Rome"])
    zodiac_type: ZodiacType = Field(
        default="Tropical",
        description="Zodiac type used for the calculation.",
        examples=list(get_args(ZodiacType)),
    )
    sidereal_mode: Optional[SiderealMode] = Field(
        default=None,
        description="Sidereal ayanamsha used when zodiac_type is 'Sidereal'.",
        examples=[None],
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        _check_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_date(self) -> "MoonVocRequestModel":
        _check_date(self.year, self.month, self.day)
        if self.sidereal_mode and self.zodiac_type != "Sidereal":
            raise ValueError("Set zodiac_type='Sidereal' when sidereal_mode is provided.")
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            modes = ", ".join(get_args(SiderealMode))
            raise ValueError(f"sidereal_mode is required when zodiac_type='Sidereal'. Available modes: {modes}")
        return self


class DominantsRequestModel(StrictRequestModel):
    """Request payload for the dominants endpoint.

    Computes a chart's dominants (dominant planet, sign, element, modality and
    house — plus polarity, hemispheres and quadrants for the modern method) with
    the selected calculation school. The heavy lifting is done by kerykeion's
    ``DominantsFactory``; this model only describes the request surface.
    """

    model_config = {"extra": "forbid"}

    subject: SubjectModel = Field(description="Subject (birth data) to analyse.")
    strategy: DominantMethod = Field(
        default="modern",
        description=("Dominant-calculation school: 'modern' (Astrotheme-style weighted), 'almuten_figuris' (traditional Lord of the Geniture), 'elemental' (element/modality balance)."),
        examples=list(get_args(DominantMethod)),
    )
    active_points: Optional[list[Union[ActivePointName, str]]] = Field(
        default=None,
        description=(
            "Optional subset of points to compute and weigh. It is applied both when building the "
            "subject and to the 'elemental' tally, so passing a short list also narrows the points the "
            "'modern' and 'almuten_figuris' schools can see. Defaults to the chart's standard active points."
        ),
    )
    distribution_method: DistributionMethod = Field(
        default="weighted",
        description="'weighted' (default) or 'pure_count' for the element/modality tally.",
    )
    custom_distribution_weights: Optional[Mapping[str, float]] = Field(
        default=None,
        description="Optional per-point weight overrides for the element/modality tally (case-insensitive point names).",
    )
    include_accidental_dignities: bool = Field(
        default=False,
        description="Almuten Figuris only: add the optional accidental-dignity layer (house placement, weekday ruler).",
    )
    include_score_breakdown: bool = Field(
        default=False,
        description="Populate the result's 'score_breakdown' with a per-rule audit trail.",
    )

    @field_validator("active_points", mode="before")
    @classmethod
    def normalize_active_points(cls, value: Optional[list]) -> Optional[list]:
        """Canonicalize aliased point names (e.g. 'asc', 'mc', 'north_node') so
        they are not silently dropped by the factory point matcher."""
        return _normalize_active_points(value)


class NowMoonPhaseRequestModel(StrictRequestModel):
    """Request payload for the 'now' moon phase endpoint. All fields are optional."""

    model_config = {"extra": "forbid"}

    using_default_location: bool = Field(
        default=True,
        description="Flag indicating whether the location is a default fallback.",
    )
    location_precision: int = Field(
        default=0,
        description="Number of decimal places used to round latitude and longitude in the response.",
        ge=0,
        le=10,
    )


class PlanetaryReturnDataRequestModel(ChartDataConfigurationMixin):
    """Shared payload for solar and lunar return data endpoints (data only, no SVG).

    Supports two modes:

    - **Compute mode**: provide ``subject`` + search parameters (``year``/``iso_datetime``).
    - **Pre-computed mode**: provide ``chart_data`` to skip calculation.
    """

    subject: Optional[SubjectModel] = Field(
        default=None,
        description="Natal subject used for the return calculation. Required when chart_data is not provided.",
    )
    year: Optional[int] = Field(
        default=None,
        description=("Year to search for the next return (astronomical numbering: 0 = 1 BCE, -1 = 2 BCE, etc.). Supports range -13200 to 9999."),
        ge=-13200,
        le=9999,
    )
    month: Optional[int] = Field(
        default=None,
        description="Optional month (1-12) to start the search from. Used with year and day.",
        ge=1,
        le=12,
    )
    day: Optional[int] = Field(
        default=1,
        description="Optional day (1-31) to start the search from. Requires month and year.",
        ge=1,
        le=31,
    )
    iso_datetime: Optional[str] = Field(
        default=None,
        description="ISO formatted datetime used as starting point for the search.",
        examples=["2025-05-01T00:00:00+00:00"],
    )
    direction: Literal["next", "previous"] = Field(
        default="next",
        description=(
            "Search direction from the starting point. 'next' finds the upcoming return (default); 'previous' finds the most recent past return. Seeded with the instant of a return this API reported, 'next' yields the following return and 'previous' the preceding one: ordering is decided at whole-second resolution, the resolution return instants are reported at. Requires the libephemeris backend for backward search."
        ),
    )
    wheel_type: Literal["dual", "single"] = Field(
        default="dual",
        description="Return chart configuration: 'dual' wheel (natal + return) or 'single' wheel.",
    )
    include_house_comparison: bool = Field(
        default=True,
        description="Include house overlay comparison for dual wheel returns.",
    )
    return_location: Optional[ReturnLocationModel] = Field(
        default=None,
        description="Override location used for the return chart.",
    )
    chart_data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Pre-computed chart data object as returned by /chart/* or /context/* endpoints. When provided, the endpoint skips chart calculation and generates the AI context directly from this data."
        ),
    )

    @model_validator(mode="after")
    def validate_search_parameters(self) -> "PlanetaryReturnDataRequestModel":
        if self.chart_data is not None:
            return self

        if self.subject is None:
            raise ValueError("Provide either 'chart_data' (pre-computed) or 'subject' with search parameters.")

        # NOTE: explicit `is None` checks — year=0 (1 BCE) is falsy but valid.
        self.iso_datetime = _blank_to_none(self.iso_datetime)
        _validate_iso_datetime(self.iso_datetime)
        if self.year is None and self.iso_datetime is None:
            raise ValueError("Provide either 'iso_datetime' or 'year' (with optional month and day) to locate the return.")

        if self.month is not None and self.year is None:
            raise ValueError("Month can only be provided together with a year.")

        if self.day is not None and self.day != 1 and self.month is None:
            raise ValueError("Day can only be provided together with month and year.")

        if self.year is not None and self.month is not None:
            _check_date(self.year, self.month, self.day or 1)

        if self.wheel_type == "single":
            self.include_house_comparison = False

        return self


# ===========================================================================
# v6 Advanced Feature Request Models
# ===========================================================================










# Body vocabulary of the mundane aspectarian (kerykeion's canonical
# fast-to-slow order; also the point_a/point_b ordering in results).
MUNDANE_ASPECT_POINTS = (
    "Moon",
    "Mercury",
    "Venus",
    "Sun",
    "Mars",
    "Jupiter",
    "Saturn",
    "Chiron",
    "Uranus",
    "Neptune",
    "Pluto",
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
)

# Longitude-aspect vocabulary accepted by the aspectarian (kerykeion chart
# defaults). Declination aspects (parallel/contra-parallel) are not longitude
# events and are rejected.
MUNDANE_ASPECT_NAMES = (
    "conjunction",
    "semi-sextile",
    "semi-square",
    "sextile",
    "quintile",
    "square",
    "trine",
    "sesquiquadrate",
    "biquintile",
    "quincunx",
    "opposition",
)


def _validate_scan_range(start_date: str, end_date: str, max_days: int, label: str) -> None:
    """Shared start/end ISO-range validation for event-scan payloads.

    Mirrors the stations/ingresses validators: naive-UTC comparison, date-only
    end-of-day widening, OverflowError guard, span cap.
    """
    from datetime import datetime, timezone

    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError(f"start_date/end_date must be ISO dates: {exc}")
    try:
        if start.tzinfo is not None:
            start = start.astimezone(timezone.utc).replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.astimezone(timezone.utc).replace(tzinfo=None)
    except OverflowError:
        raise ValueError("start_date/end_date is out of the supported range.")
    if "T" not in end_date and "t" not in end_date and " " not in end_date:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    if end <= start:
        raise ValueError("end_date must be after start_date.")
    if (end - start).days > max_days:
        raise ValueError(f"Range too large; maximum span is {label}.")
