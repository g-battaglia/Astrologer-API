"""Events API endpoints."""

import asyncio
from datetime import datetime
from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import (
    EclipseFactory,
    LunationFinderFactory,
    MundaneAspectFactory,
    PlanetaryPhenomenaFactory,
    RetrogradeStationFactory,
    SignIngressFactory,
)
from ..types.request_models import (
    EclipseSearchRequestModel,
    HeliacalEventsRequestModel,
    LunationsRequestModel,
    MundaneAspectsRequestModel,
    OccultationSearchRequestModel,
    PlanetaryPhenomenaRequestModel,
    RetrogradeStationsRequestModel,
    SignIngressesRequestModel,
)
from ..types.response_models import (
    EclipseSearchResponseModel,
    LunationsResponseModel,
    HeliacalEventsResponseModel,
    MundaneAspectsResponseModel,
    OccultationSearchResponseModel,
    PlanetaryPhenomenaResponseModel,
    RetrogradeStationsResponseModel,
    SignIngressesResponseModel,
)
from ..utils.router_utils import (
    build_subject,
    dump,
    handle_exception,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body
from ..utils.occultation import (
    HELIACAL_SEARCH_TIMEOUT_S,
    OCCULTATION_PLANET_IDS,
    OCCULTATION_SEARCH_TIMEOUT_S,
    run_heliacal_search,
    run_occultation_search,
)
from ..utils.subject_kwargs import subject_factory_kwargs

logger = getLogger(__name__)
router = APIRouter()


def _yearly_chunks(start_date: str, end_date: str) -> "list[tuple[str, str]]":
    """Split ``[start_date, end_date]`` into <=1-year (start, end) string pairs.

    The original endpoints are kept at the extremes so the factory's own
    date-only / datetime semantics are preserved; interior bounds are explicit
    datetimes, so chunks abut without gaps or overlaps.
    """
    from datetime import datetime, timedelta, timezone

    def naive(s: str) -> datetime:
        d = datetime.fromisoformat(s)
        if d.tzinfo is not None:
            d = d.astimezone(timezone.utc).replace(tzinfo=None)
        return d

    start = naive(start_date)
    end = naive(end_date)
    if "T" not in end_date and "t" not in end_date and " " not in end_date:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    if end <= start:
        return [(start_date, end_date)]

    edges: "list[tuple[datetime, datetime]]" = []
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=365), end)
        edges.append((cur, nxt))
        cur = nxt

    last = len(edges) - 1
    return [
        (
            start_date if i == 0 else a.isoformat(),
            end_date if i == last else b.isoformat(),
        )
        for i, (a, b) in enumerate(edges)
    ]


async def _scan_chunked(factory, attr: str, start_date: str, end_date: str, planets):
    """Run ``factory.from_iso_range`` over yearly chunks in a worker thread,
    yielding between chunks so the process-wide EPHEMERIS_LOCK is released and the
    event loop (and /health) stays responsive during a long scan. Concatenated
    results stay chronologically ordered (chunks are sequential, each ordered).

    Chunks go through ``run_heavy`` so the scan competes for the same bounded
    pool as every other heavy computation — ``asyncio.to_thread`` would fan
    concurrent scans out onto the unbounded default executor, bypassing the
    HEAVY_MAX_WORKERS memory cap."""
    items: list = []
    for chunk_start, chunk_end in _yearly_chunks(start_date, end_date):
        part = await run_heavy(factory.from_iso_range, chunk_start, chunk_end, planets)
        items.extend(getattr(part, attr))
        await asyncio.sleep(0)
    return items


@router.post("/api/v6/events/eclipses", response_model=EclipseSearchResponseModel, operation_id="advancedEclipses")
async def eclipse_search(request_body: EclipseSearchRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/eclipses`

    Search for upcoming solar and lunar eclipses, either globally or for a specific location.

    **Parameters:**
    - `latitude`, `longitude`: Location for local search (omit both for global).
    - `start_year`: Year to start searching from (default 2025).
    - `count`: Number of eclipses of each type to find (default 5): `count=2`
      returns up to 2 solar plus 2 lunar eclipses.

    **Returns:**
    - `solar_eclipses`: List of solar eclipse events.
    - `lunar_eclipses`: List of lunar eclipse events.
    - `latitude`, `longitude`: Echo of the request location (null on global searches).
    """
    log_request_with_body(logger, request, "Eclipse search request", request_body.model_dump_json())

    try:
        if request_body.latitude is not None and request_body.longitude is not None:
            result = await run_heavy(
                EclipseFactory.search_from_location,
                lat=request_body.latitude,
                lng=request_body.longitude,
                start_year=request_body.start_year,
                count=request_body.count,
            )
        else:
            result = await run_heavy(
                EclipseFactory.search_global,
                start_year=request_body.start_year,
                count=request_body.count,
            )

        return JSONResponse(
            content={
                "status": "OK",
                "solar_eclipses": dump(result.solar_eclipses),
                "lunar_eclipses": dump(result.lunar_eclipses),
                "latitude": getattr(result, "latitude", request_body.latitude),
                "longitude": getattr(result, "longitude", request_body.longitude),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/lunations", response_model=LunationsResponseModel, operation_id="advancedLunations")
async def lunations(request_body: LunationsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/lunations`

    Find lunations (New Moon, First Quarter, Full Moon, Last Quarter) within a
    date range, ordered chronologically, each with the Sun and Moon zodiac
    positions at the exact phase.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (treated as UTC).
    - `phases`: Optional subset of `new`/`first_quarter`/`full`/`last_quarter`.

    **Returns:**
    - `lunations`: Ordered list of lunation events.
    """
    log_request_with_body(logger, request, "Lunations request", request_body.model_dump_json())

    try:
        result = await run_heavy(
            LunationFinderFactory.from_iso_range,
            start_date=request_body.start_date,
            end_date=request_body.end_date,
            phases=request_body.phases,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "start_jd": result.start_jd,
                "end_jd": result.end_jd,
                "lunations": dump(result.lunations),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/retrograde-stations", response_model=RetrogradeStationsResponseModel, operation_id="advancedRetrogradeStations")
async def retrograde_stations(request_body: RetrogradeStationsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/retrograde-stations`

    Find planetary retrograde/direct stations (motion reversals) within a date
    range, ordered chronologically, each with the zodiac position at the station.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (treated as UTC).
    - `planets`: Optional subset of Mercury..Pluto (the Sun and Moon never station).

    **Returns:**
    - `stations`: Ordered list of stations (SR = retrograde, SD = direct).
    """
    log_request_with_body(logger, request, "Retrograde stations request", request_body.model_dump_json())

    try:
        # Scan in yearly chunks on a worker thread, releasing EPHEMERIS_LOCK
        # between chunks so the single-worker event loop stays responsive.
        stations = await _scan_chunked(
            RetrogradeStationFactory,
            "stations",
            request_body.start_date,
            request_body.end_date,
            request_body.planets,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "stations": dump(stations),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/sign-ingresses", response_model=SignIngressesResponseModel, operation_id="advancedSignIngresses")
async def sign_ingresses(request_body: SignIngressesRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/sign-ingresses`

    Find zodiac sign ingresses (30 degree boundary crossings) within a date
    range, ordered chronologically. Retrograde re-entries are included.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (treated as UTC).
    - `planets`: Optional subset of Sun..Pluto plus Moon (Moon is opt-in).

    **Returns:**
    - `ingresses`: Ordered list of sign ingresses with from/to signs.
    """
    log_request_with_body(logger, request, "Sign ingresses request", request_body.model_dump_json())

    try:
        # Scan in yearly chunks on a worker thread, releasing EPHEMERIS_LOCK
        # between chunks so the single-worker event loop stays responsive.
        ingresses = await _scan_chunked(
            SignIngressFactory,
            "ingresses",
            request_body.start_date,
            request_body.end_date,
            request_body.planets,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "ingresses": dump(ingresses),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/mundane-aspects", response_model=MundaneAspectsResponseModel, operation_id="advancedMundaneAspects")
async def mundane_aspects(request_body: MundaneAspectsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/mundane-aspects`

    Find every exact mundane (transiting-to-transiting) aspect within a date
    range — the *aspectarian* of a printed astrological calendar — ordered
    chronologically, each with its exact UTC instant, both bodies' zodiac
    positions and retrograde flags.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (treated as UTC, max ~1 year).
    - `points`: Optional body subset. Defaults to Sun..Pluto; the Moon is opt-in.
    - `aspects`: Optional aspect names. Defaults to the five Ptolemaic majors.
    - `zodiac_type`, `sidereal_mode`: Zodiac for the reported longitudes/signs
      (aspect instants are zodiac-independent).

    **Returns:**
    - `aspects`: Ordered list of exact aspects.
    """
    log_request_with_body(logger, request, "Mundane aspects request", request_body.model_dump_json())

    try:
        result = await run_heavy(
            MundaneAspectFactory.from_iso_range,
            request_body.start_date,
            request_body.end_date,
            request_body.points,
            request_body.aspects,
            request_body.zodiac_type,
            request_body.sidereal_mode,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "aspects": dump(result.aspects),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/planetary-phenomena", response_model=PlanetaryPhenomenaResponseModel, operation_id="advancedPlanetaryPhenomena")
async def planetary_phenomena(request_body: PlanetaryPhenomenaRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/planetary-phenomena`

    Compute observational phenomena (phase angle, elongation, magnitude, morning/evening star)
    for planets at a given moment.

    Each entry also carries its `solar_phase` — the traditional classification of a planet's
    proximity to the Sun: `cazimi` (within 17 arcminutes), `combust` (within 8°30'),
    `under_the_beams` (within 17°) or `free`.

    **Parameters:**
    - `subject`: Subject defining the calculation moment.
    - `planets`: Optional list of planet names to filter.
    - `solar_phase_thresholds`: Optional override of the cazimi / combust / under-the-beams band half-widths.

    **Returns:**
    - `phenomena`: List of planetary phenomena data, each carrying its `solar_phase`.
    - `solar_phase_thresholds`: The half-widths that produced those classifications.
    """
    log_request_with_body(logger, request, "Planetary phenomena request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)
        # Held back unless the caller sent it: an engine that predates the
        # keyword answers an unknown kwarg with a TypeError, i.e. a 500 on the
        # whole endpoint rather than an ignored option.
        extra_kwargs = {}
        if request_body.solar_phase_thresholds is not None:
            from kerykeion.schemas import SolarPhaseThresholdsModel

            extra_kwargs["solar_phase_thresholds"] = SolarPhaseThresholdsModel(**request_body.solar_phase_thresholds.model_dump())
        result = await run_heavy(
            PlanetaryPhenomenaFactory.from_subject,
            subject,
            planets=request_body.planets,
            **extra_kwargs,
        )

        thresholds = getattr(result, "solar_phase_thresholds", None)
        return JSONResponse(
            content={
                "status": "OK",
                "iso_datetime": getattr(result, "iso_datetime", None),
                "julian_day": getattr(result, "julian_day", None),
                "phenomena": dump(result.phenomena),
                "solar_phase_thresholds": dump(thresholds) if thresholds is not None else None,
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/heliacal-events", response_model=HeliacalEventsResponseModel, operation_id="advancedHeliacalEvents")
async def heliacal_events(request_body: HeliacalEventsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/heliacal-events`

    Search for heliacal rising/setting events (first/last visibility) for planets and stars.

    **Parameters:**
    - `subject`: Subject defining the starting moment and observation location.
    - `count`: Number of events to return (default 5, max 20; `count` times the
      number of event types may not exceed 40).
    - `planets`: Optional list of planet/star names (max 12).
    - `event_types`: Optional subset of `heliacal_rising`, `heliacal_setting`,
      `evening_first`, `morning_last` (default: rising + setting; the last two
      apply only to Mercury and Venus).

    **Returns:**
    - `events`: List of heliacal events.
    """
    log_request_with_body(logger, request, "Heliacal events request", request_body.model_dump_json())

    try:
        event_types = None
        if request_body.event_types:
            label_to_int = {
                "heliacal_rising": 1,
                "heliacal_setting": 2,
                "evening_first": 3,
                "morning_last": 4,
            }
            event_types = [label_to_int[e] for e in request_body.event_types]
        # Native heliacal searches cannot be interrupted in a thread. The full
        # subject-build + search therefore runs under the same bounded spawn
        # budget as occultations and is hard-killed at the advertised ceiling.
        events = await run_heliacal_search(
            timeout=HELIACAL_SEARCH_TIMEOUT_S,
            subject_kwargs=subject_factory_kwargs(request_body.subject),
            count=request_body.count,
            planets=request_body.planets,
            event_types=event_types,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "events": dump(events),
            },
            status_code=200,
        )

    except TimeoutError:
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": "Heliacal search timed out. Reduce planets, count, or event_types.",
                "error_type": "TimeoutError",
            },
            status_code=504,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/occultations", response_model=OccultationSearchResponseModel, operation_id="advancedOccultations")
async def occultation_search(request_body: OccultationSearchRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/occultations`

    Search for lunar occultations of a planet, visible from the observer location.

    **Parameters:**
    - `subject`: Subject defining the starting moment and observation location.
    - `planet`: Occulted body — the planet the Moon passes in front of (default 'Venus').
    - `count`: Number of events to return (default 5).

    **Returns:**
    - `events`: List of occultation events.
    """
    log_request_with_body(logger, request, "Occultation search request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        planet_id = OCCULTATION_PLANET_IDS[request_body.planet]

        events = await run_occultation_search(
            "local",
            timeout=OCCULTATION_SEARCH_TIMEOUT_S,
            julian_day=subject.julian_day,
            planet_id=planet_id,
            lat=subject.lat,
            lng=subject.lng,
            count=request_body.count,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "events": dump(events),
            },
            status_code=200,
        )

    except TimeoutError:
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": "Occultation search timed out. Try reducing 'count'.",
                "error_type": "TimeoutError",
            },
            status_code=504,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/events/occultations/global", response_model=OccultationSearchResponseModel, operation_id="advancedOccultationsGlobal")
async def occultation_search_global(request_body: OccultationSearchRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/events/occultations/global`

    Search for lunar occultations of a planet globally (not location-specific).

    **Parameters:**
    - `subject`: Subject defining the starting Julian Day.
    - `planet`: Occulted body — the planet the Moon passes in front of (default 'Venus').
    - `count`: Number of events to return.

    **Returns:**
    - `events`: List of global occultation events.
    """
    log_request_with_body(logger, request, "Global occultation search request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        planet_id = OCCULTATION_PLANET_IDS[request_body.planet]

        events = await run_occultation_search(
            "global",
            timeout=OCCULTATION_SEARCH_TIMEOUT_S,
            julian_day=subject.julian_day,
            planet_id=planet_id,
            count=request_body.count,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "events": dump(events),
            },
            status_code=200,
        )

    except TimeoutError:
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": "Occultation search timed out. Try reducing 'count'.",
                "error_type": "TimeoutError",
            },
            status_code=504,
        )
    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
