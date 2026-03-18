from __future__ import annotations

from logging import getLogger
from typing import Optional, Sequence, Union

from fastapi import Request
from fastapi.responses import JSONResponse
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    MoonPhaseDetailsFactory,
    to_context,
)
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import ActiveAspect, KerykeionException
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_ASPECTS,
    DEFAULT_ACTIVE_POINTS,
)

from kerykeion.schemas.kr_models import MoonPhaseOverviewModel

from ..types.request_models import (
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
)

logger = getLogger(__name__)

GEONAMES_ERROR_MESSAGE = (
    "City/Nation name error or invalid GeoNames username. Please check your username or city name and try again. "
    "You can create a free username here: https://www.geonames.org/login/. If you want to bypass the usage of "
    "GeoNames, please remove the geonames_username field from the request. Note: The nation field should be the "
    "country code (e.g. US, UK, FR, DE, etc.)."
)

GEONAMES_ERROR_KEYWORDS = (
    "No data found for this city",
    "data found for this city",
    "Missing data from geonames",
    "You need to set the coordinates",
    "Check your connection",
)


def normalize_coordinate(value: Optional[float]) -> Optional[float]:
    """
    Normalize coordinate values to avoid zero division or other numerical issues.

    Args:
        value (Optional[float]): The coordinate value to normalize.

    Returns:
        Optional[float]: The normalized coordinate value, or None if input is None.
                         Values close to zero are adjusted to +/- 1e-6.
    """
    if value is None:
        return None
    if abs(value) < 1e-6:
        return 1e-6 if value >= 0 else -1e-6
    return value


def dump(value: object) -> object:
    """
    Recursively dump Pydantic models to dictionaries.

    Args:
        value: The value to dump (can be a Pydantic model, list, tuple, or primitive).

    Returns:
        The dumped value as a dictionary or primitive type.
    """
    if isinstance(value, list):
        return [dump(item) for item in value]
    if isinstance(value, tuple):
        return tuple(dump(item) for item in value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def resolve_nation(value: Optional[str]) -> Optional[str]:
    """
    Resolve nation code to uppercase or None.

    Args:
        value (Optional[str]): The nation code.

    Returns:
        Optional[str]: The uppercase nation code, or None if input is invalid/null.
    """
    if not value or value.lower() == "null":
        return None
    return value.upper()


def resolve_active_points(points: Optional[Sequence[str]]) -> list[str]:
    """
    Resolve active points, falling back to defaults if not provided.

    Args:
        points (Optional[Sequence[str]]): List of active points.

    Returns:
        list[str]: The resolved list of active points.
    """
    if points:
        return list(points)
    return list(DEFAULT_ACTIVE_POINTS)


def resolve_active_aspects(aspects: Optional[Sequence[ActiveAspect]]) -> list[dict]:
    """
    Resolve active aspects, falling back to defaults if not provided.

    Args:
        aspects (Optional[Sequence[ActiveAspect]]): List of active aspects.

    Returns:
        list[dict]: The resolved list of active aspects as dictionaries.
    """
    if aspects:
        return [dict(aspect) for aspect in aspects]
    return [dict(item) for item in DEFAULT_ACTIVE_ASPECTS]


def build_subject(
    subject_request: SubjectModel, *, active_points: Optional[Sequence[str]] = None
) -> object:
    """
    Build an AstrologicalSubject instance from a request model.

    Args:
        subject_request (SubjectModel): The subject data from the request.
        active_points (Optional[Sequence[str]]): Optional list of active points to override defaults.

    Returns:
        AstrologicalSubject: The constructed astrological subject.
    """
    resolved_points = resolve_active_points(active_points)
    online = bool(subject_request.geonames_username)

    return AstrologicalSubjectFactory.from_birth_data(
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
    )


def build_transit_subject(
    transit_request,
    reference_subject,
    *,
    active_points: Optional[Sequence[str]] = None,
    custom_ayanamsa_t0: Optional[float] = None,
    custom_ayanamsa_ayan_t0: Optional[float] = None,
) -> object:
    """
    Build a Transit Subject instance, inheriting settings from a reference subject.

    Args:
        transit_request: The transit data request model.
        reference_subject: The reference (natal) subject to inherit settings from.
        active_points (Optional[Sequence[str]]): Optional list of active points.
        custom_ayanamsa_t0: Reference epoch for USER sidereal mode (from natal subject request).
        custom_ayanamsa_ayan_t0: Ayanamsa offset for USER sidereal mode (from natal subject request).

    Returns:
        AstrologicalSubject: The constructed transit subject.
    """
    resolved_points = resolve_active_points(active_points)
    online = bool(transit_request.geonames_username)

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
    )


def render_chart(
    chart_data,
    theme: Optional[str],
    language: Optional[str],
    split_chart: bool = False,
    transparent_background: bool = False,
    show_house_position_comparison: bool = True,
    show_cusp_position_comparison: bool = True,
    show_degree_indicators: bool = True,
    show_aspect_icons: bool = True,
    custom_title: Optional[str] = None,
    style: str = "classic",
    show_zodiac_background_ring: bool = True,
    double_chart_aspect_grid_type: str = "list",
) -> dict:
    """
    Render chart(s) based on configuration.

    Args:
        chart_data: The chart data object.
        theme (Optional[str]): The visual theme for the chart.
        language (Optional[str]): The language for chart labels.
        split_chart (bool): Whether to return separate wheel and grid SVGs.
        transparent_background (bool): Whether the chart background should be transparent.
        show_house_position_comparison (bool): Whether to show house comparison table.
        show_cusp_position_comparison (bool): Whether to show cusp position comparison table (dual charts).
        show_degree_indicators (bool): Whether to show radial lines and degree numbers for planets.
        show_aspect_icons (bool): Whether to show aspect icons on aspect lines.
        custom_title (Optional[str]): Custom title for the chart.
        style (str): Chart rendering style — 'classic' (traditional wheel) or 'modern' (concentric rings).
        show_zodiac_background_ring (bool): Show colored zodiac sign wedges (modern style only).
        double_chart_aspect_grid_type (str): Layout for double-chart aspects — 'list' or 'table'.

    Returns:
        dict: The complete payload with chart data and SVG strings.
    """
    drawer = ChartDrawer(
        chart_data=chart_data,
        theme=theme or "classic",
        chart_language=language or "EN",
        transparent_background=transparent_background,
        show_house_position_comparison=show_house_position_comparison,
        show_cusp_position_comparison=show_cusp_position_comparison,
        show_degree_indicators=show_degree_indicators,
        show_aspect_icons=show_aspect_icons,
        custom_title=custom_title,
        double_chart_aspect_grid_type=double_chart_aspect_grid_type,
        style=style,
        show_zodiac_background_ring=show_zodiac_background_ring,
    )

    if split_chart:
        return {
            "chart_wheel": drawer.generate_wheel_only_svg_string(minify=True),
            "chart_grid": drawer.generate_aspect_grid_only_svg_string(minify=True),
        }
    else:
        return {"chart": drawer.generate_svg_string(minify=True)}


def chart_data_payload(chart_data) -> dict:
    """
    Wrap chart data in a standard response payload.

    Args:
        chart_data: The chart data object.

    Returns:
        dict: The response payload containing status and dumped chart data.
    """
    return {
        "status": "OK",
        "chart_data": dump(chart_data),
    }


def chart_payload(
    chart_data,
    theme: Optional[str],
    language: Optional[str],
    split_chart: bool = False,
    transparent_background: bool = False,
    show_house_position_comparison: bool = True,
    show_cusp_position_comparison: bool = True,
    show_degree_indicators: bool = True,
    show_aspect_icons: bool = True,
    custom_title: Optional[str] = None,
    style: str = "classic",
    show_zodiac_background_ring: bool = True,
    double_chart_aspect_grid_type: str = "list",
) -> dict:
    """
    Generate a complete chart payload including data and rendered SVG(s).

    Args:
        chart_data: The chart data object.
        theme (Optional[str]): The visual theme for the chart.
        language (Optional[str]): The language for chart labels.
        split_chart (bool): Whether to return separate wheel and grid SVGs.
        transparent_background (bool): Whether the chart background should be transparent.
        show_house_position_comparison (bool): Whether to show house comparison table.
        show_cusp_position_comparison (bool): Whether to show cusp position comparison table (dual charts).
        show_degree_indicators (bool): Whether to show radial lines and degree numbers for planets.
        show_aspect_icons (bool): Whether to show aspect icons on aspect lines.
        custom_title (Optional[str]): Custom title for the chart.
        style (str): Chart rendering style — 'classic' (traditional wheel) or 'modern' (concentric rings).
        show_zodiac_background_ring (bool): Show colored zodiac sign wedges (modern style only).
        double_chart_aspect_grid_type (str): Layout for double-chart aspects — 'list' or 'table'.

    Returns:
        dict: The complete payload with chart data and SVG strings.
    """
    payload = chart_data_payload(chart_data)
    charts = render_chart(
        chart_data,
        theme,
        language,
        split_chart,
        transparent_background,
        show_house_position_comparison,
        show_cusp_position_comparison,
        show_degree_indicators,
        show_aspect_icons,
        custom_title,
        style,
        show_zodiac_background_ring,
        double_chart_aspect_grid_type,
    )
    payload.update(charts)
    return payload


def subject_context_payload(subject) -> dict:
    """
    Wrap subject data with AI-optimized context in a standard response payload.

    Args:
        subject: The astrological subject object.

    Returns:
        dict: The response payload containing status, subject_context, and subject.
    """
    return {
        "status": "OK",
        "subject_context": to_context(subject),
        "subject": dump(subject),
    }


def context_payload(chart_data) -> dict:
    """
    Wrap chart data with AI-optimized context in a standard response payload.

    Args:
        chart_data: The chart data object.

    Returns:
        dict: The response payload containing status, context, and chart_data.
    """
    return {
        "status": "OK",
        "context": to_context(chart_data),
        "chart_data": dump(chart_data),
    }


async def handle_exception(exc: Exception, request: Request) -> JSONResponse:
    """
    Handle exceptions and return appropriate JSON responses.

    Args:
        exc (Exception): The exception raised.
        request (Request): The incoming request object.

    Returns:
        JSONResponse: The error response with appropriate status code and message.
    """
    message = str(exc).strip() or exc.__class__.__name__

    # Log the complete request body for debugging
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else "Empty body"
        logger.error(
            f"{request.url}: {message} | Request body: {body_str}", exc_info=True
        )
    except Exception as body_exc:
        logger.error(
            f"{request.url}: {message} | Failed to read request body: {body_exc}",
            exc_info=True,
        )

    if any(keyword in message for keyword in GEONAMES_ERROR_KEYWORDS):
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": GEONAMES_ERROR_MESSAGE,
            },
            status_code=400,
        )

    status_code = 400 if isinstance(exc, KerykeionException) else 500
    return JSONResponse(
        content={
            "status": "ERROR",
            "message": message,
            "error_type": exc.__class__.__name__,
        },
        status_code=status_code,
    )


def build_return_factory(
    natal_subject,
    request_body: Union[PlanetaryReturnRequestModel, PlanetaryReturnDataRequestModel],
) -> PlanetaryReturnFactory:
    """
    Build a PlanetaryReturnFactory based on request parameters.

    Args:
        natal_subject: The natal subject.
        request_body: The request body containing return location and settings.

    Returns:
        PlanetaryReturnFactory: The factory instance for calculating returns.
    """
    location = request_body.return_location

    # Extract custom ayanamsa params from the natal subject request for USER sidereal mode
    custom_ayanamsa_kwargs: dict = {}
    if hasattr(request_body, "subject") and hasattr(
        request_body.subject, "custom_ayanamsa_t0"
    ):
        if request_body.subject.custom_ayanamsa_t0 is not None:
            custom_ayanamsa_kwargs["custom_ayanamsa_t0"] = (
                request_body.subject.custom_ayanamsa_t0
            )
        if request_body.subject.custom_ayanamsa_ayan_t0 is not None:
            custom_ayanamsa_kwargs["custom_ayanamsa_ayan_t0"] = (
                request_body.subject.custom_ayanamsa_ayan_t0
            )

    if location:
        nation = resolve_nation(location.nation) or natal_subject.nation

        if (
            location.geonames_username
            or location.latitude is None
            or location.longitude is None
            or location.timezone is None
        ):
            logger.info(
                "Building return factory with GeoNames (online mode) for location: %s, %s",
                location.city or natal_subject.city,
                nation,
            )
            return PlanetaryReturnFactory(
                natal_subject,
                city=location.city or natal_subject.city,
                nation=nation,
                online=True,
                geonames_username=location.geonames_username,
                cache_expire_after_days=30,
                altitude=location.altitude,
                **custom_ayanamsa_kwargs,
            )

        logger.info(
            "Building return factory with explicit coordinates (offline mode) for location: %s, %s (lat=%.4f, lng=%.4f)",
            location.city or natal_subject.city,
            nation,
            location.latitude,
            location.longitude,
        )
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
        )

    logger.info(
        "Building return factory using natal subject location (offline mode): %s, %s",
        natal_subject.city,
        natal_subject.nation,
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
        **custom_ayanamsa_kwargs,
    )


def calculate_return_chart_data(
    request_body: Union[PlanetaryReturnRequestModel, PlanetaryReturnDataRequestModel],
    return_type: str,
):
    """
    Calculate return chart data (Solar or Lunar).

    Args:
        request_body: The request body containing return parameters.
        return_type (str): The type of return ("Solar" or "Lunar").

    Returns:
        The calculated chart data.

    Raises:
        KerykeionException: If required parameters (year/month) are missing.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)

    natal_subject = build_subject(request_body.subject, active_points=active_points)
    return_factory = build_return_factory(natal_subject, request_body)

    if request_body.iso_datetime:
        return_subject = return_factory.next_return_from_iso_formatted_time(
            request_body.iso_datetime, return_type
        )  # type: ignore[arg-type]
    elif request_body.month:
        if request_body.year is None:
            raise KerykeionException("Year must be provided when month is specified.")
        return_subject = return_factory.next_return_from_date(
            request_body.year,
            request_body.month,
            request_body.day or 1,
            return_type=return_type,
        )
    else:
        if request_body.year is None:
            raise KerykeionException(
                "Year must be provided when iso_datetime is not set."
            )
        return_subject = return_factory.next_return_from_date(
            request_body.year, 1, 1, return_type=return_type
        )

    if request_body.wheel_type == "dual":
        chart_data = ChartDataFactory.create_return_chart_data(
            natal_subject,
            return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=request_body.include_house_comparison,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )
    else:
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(
            return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            distribution_method=request_body.distribution_method,
            custom_distribution_weights=request_body.custom_distribution_weights,
        )

    return chart_data


def create_natal_chart_data(
    request_body: Union[BirthChartRequestModel, BirthChartDataRequestModel],
) -> SingleChartDataModel:
    """
    Create natal chart data from request.

    Args:
        request_body: The request body containing subject and calculation parameters.

    Returns:
        The calculated natal chart data.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    subject = build_subject(request_body.subject, active_points=active_points)
    chart_data = ChartDataFactory.create_natal_chart_data(
        subject,
        active_points=active_points,
        active_aspects=active_aspects,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_synastry_chart_data(
    request_body: Union[SynastryChartRequestModel, SynastryChartDataRequestModel],
) -> DualChartDataModel:
    """
    Create synastry chart data from request.

    Args:
        request_body: The request body containing two subjects and calculation parameters.

    Returns:
        The calculated synastry chart data.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    first_subject = build_subject(
        request_body.first_subject, active_points=active_points
    )
    second_subject = build_subject(
        request_body.second_subject, active_points=active_points
    )
    chart_data = ChartDataFactory.create_synastry_chart_data(
        first_subject,
        second_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        include_house_comparison=request_body.include_house_comparison,
        include_relationship_score=request_body.include_relationship_score,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_transit_chart_data(
    request_body: Union[TransitChartRequestModel, TransitChartDataRequestModel],
) -> DualChartDataModel:
    """
    Create transit chart data from request.

    Args:
        request_body: The request body containing natal subject, transit subject, and parameters.

    Returns:
        The calculated transit chart data.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    natal_subject = build_subject(
        request_body.first_subject, active_points=active_points
    )
    transit_subject = build_transit_subject(
        request_body.transit_subject,
        reference_subject=natal_subject,
        active_points=active_points,
        custom_ayanamsa_t0=request_body.first_subject.custom_ayanamsa_t0,
        custom_ayanamsa_ayan_t0=request_body.first_subject.custom_ayanamsa_ayan_t0,
    )
    chart_data = ChartDataFactory.create_transit_chart_data(
        natal_subject,
        transit_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        include_house_comparison=request_body.include_house_comparison,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_composite_chart_data(
    request_body: Union[CompositeChartRequestModel, CompositeChartDataRequestModel],
) -> SingleChartDataModel:
    """
    Create composite chart data from request.

    Args:
        request_body: The request body containing two subjects and parameters.

    Returns:
        The calculated composite chart data.
    """
    active_points = resolve_active_points(request_body.active_points)
    active_aspects = resolve_active_aspects(request_body.active_aspects)
    first_subject = build_subject(
        request_body.first_subject, active_points=active_points
    )
    second_subject = build_subject(
        request_body.second_subject, active_points=active_points
    )
    composite_subject = CompositeSubjectFactory(
        first_subject, second_subject
    ).get_midpoint_composite_subject_model()
    chart_data = ChartDataFactory.create_composite_chart_data(
        composite_subject,
        active_points=active_points,
        active_aspects=active_aspects,
        distribution_method=request_body.distribution_method,
        custom_distribution_weights=request_body.custom_distribution_weights,
    )
    return chart_data


def create_moon_phase_overview(
    request_body: MoonPhaseRequestModel,
) -> MoonPhaseOverviewModel:
    """
    Build a minimal AstrologicalSubject from flat moon phase request fields
    and compute a detailed moon phase overview.

    Args:
        request_body: The request body containing date/time and location fields.

    Returns:
        MoonPhaseOverviewModel: The detailed moon phase overview.
    """
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


def _format_coordinate(value: str, precision: int) -> str:
    """
    Round a coordinate string to the given number of decimal places.

    Handles edge cases like ``-0`` by normalising the sign.

    Args:
        value: The coordinate as a string (e.g. ``"51.477928"``).
        precision: Number of decimal places (0 = integer).

    Returns:
        The rounded coordinate as a string.
    """
    rounded = round(float(value), precision)

    # Normalise negative zero (e.g. round(-0.001, 0) → -0.0)
    if rounded == 0.0:
        rounded = 0.0

    if precision == 0:
        return str(int(rounded))

    return f"{rounded:.{precision}f}"


def moon_phase_payload(overview) -> dict:
    """
    Wrap a moon phase overview in a standard response payload.

    Post-processes ``location.latitude`` and ``location.longitude`` so they
    are rounded to ``location.precision`` decimal places, making the
    ``location_precision`` request parameter effective.

    Args:
        overview: The MoonPhaseOverviewModel instance.

    Returns:
        dict: The response payload containing status and dumped overview.
    """
    data = dump(overview)

    location = data.get("location")
    if location:
        precision = location.get("precision", 0)
        location["latitude"] = _format_coordinate(location["latitude"], precision)
        location["longitude"] = _format_coordinate(location["longitude"], precision)

    return {
        "status": "OK",
        "moon_phase_overview": data,
    }


def moon_phase_context_payload(overview) -> dict:
    """
    Wrap a moon phase overview with AI-optimized context in a standard response payload.

    The returned dict places *context* before *moon_phase_overview* so that
    the field ordering is consistent with the other context endpoints.

    Args:
        overview: The MoonPhaseOverviewModel instance.

    Returns:
        dict: The response payload containing status, context, and moon_phase_overview.
    """
    data_payload = moon_phase_payload(overview)
    return {
        "status": data_payload["status"],
        "context": to_context(overview),
        "moon_phase_overview": data_payload["moon_phase_overview"],
    }
