"""Traditional API endpoints."""

from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import (
    ZodiacalReleasingFactory,
    ProfectionsFactory,
    FirdariaFactory,
    HoraryIndicatorsFactory,
)
from ..types.request_models import (
    ZodiacalReleasingRequestModel,
    ProfectionsRequestModel,
    FirdariaRequestModel,
    HoraryIndicatorsRequestModel,
)
from ..types.response_models import (
    ZodiacalReleasingResponseModel,
    ProfectionsResponseModel,
    FirdariaResponseModel,
    HoraryIndicatorsResponseModel,
)
from ..utils.router_utils import (
    build_subject,
    dump,
    handle_exception,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/traditional/zodiacal-releasing", response_model=ZodiacalReleasingResponseModel, operation_id="advancedZodiacalReleasing")
async def zodiacal_releasing(request_body: ZodiacalReleasingRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/traditional/zodiacal-releasing`

    Compute zodiacal releasing (aphesis) from the Part of Fortune or Spirit.
    Periods unfold from the lot's sign in zodiacal order — each sign ruling for
    its general years and subdividing into months, days and finer levels, with
    the "loosing of the bond" jump applied as the sequence circles back.

    **Parameters:**
    - `subject`: Natal subject (requires a known birth time).
    - `lot`: `fortune` or `spirit`.
    - `levels`: Subdivision levels (1-4). L1/L2 are built in full; deeper levels
      only along the target-date path.
    - `target_date`: ISO date (`YYYY-MM-DD`) used to mark the current period chain.
    - `life_cap_years`: Upper bound (in years) on how far the sequence is
      unrolled (default 100, max 120).

    **Returns:**
    - `zodiacal_releasing`: Lot, lot sign + degree, nested periods, current path.
    """
    log_request_with_body(logger, request, "Zodiacal releasing request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        result = await run_heavy(
            ZodiacalReleasingFactory.from_subject,
            subject,
            lot=request_body.lot,
            levels=request_body.levels,
            target_date=request_body.target_date,
            life_cap_years=request_body.life_cap_years,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "zodiacal_releasing": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/traditional/profections", response_model=ProfectionsResponseModel, operation_id="advancedProfections")
async def profections(request_body: ProfectionsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/traditional/profections`

    Compute annual profections — the Hellenistic year-lord technique. Each
    completed year of life activates one house counted from the Ascendant
    (age 0 = 1st house), cycling every twelve years; the Lord of the Year is
    the traditional ruler of the sign on the profected house's cusp, in the
    subject's own house system.

    **Parameters:**
    - `subject`: Natal subject (requires the twelve house cusps).
    - `target_date`: ISO date (`YYYY-MM-DD`) the current year is resolved
      against. Defaults to today in the subject's timezone.
    - `years_before` / `years_after`: The window of years around the current one.

    **Returns:**
    - `profections`: The current profection year and the surrounding window.
    """
    log_request_with_body(logger, request, "Profections request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        result = await run_heavy(
            ProfectionsFactory.from_subject,
            subject,
            target_date=request_body.target_date,
            years_before=request_body.years_before,
            years_after=request_body.years_after,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "profections": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/traditional/firdaria", response_model=FirdariaResponseModel, operation_id="advancedFirdaria")
async def firdaria(request_body: FirdariaRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/traditional/firdaria`

    Compute the firdaria (Persian time-lord) periods. Life divides into a
    fixed 75-year sequence of planetary periods whose order depends on the
    chart's sect — day charts open with the Sun, night charts with the Moon.
    Each planetary period subdivides into seven sub-periods opening with its
    own lord; the two node periods close the cycle undivided.

    **Parameters:**
    - `subject`: Natal subject. Requires a real sect (`is_diurnal`); a midpoint
      composite has no horizon and is rejected.
    - `target_date`: ISO date (`YYYY-MM-DD`) the current period is resolved
      against. Defaults to now in the subject's timezone.
    - `life_cap_years`: How far the timeline is unrolled (default 120).

    **Returns:**
    - `firdaria`: Sect, the major periods with sub-periods, and the current
      period/sub-period pointers.
    """
    log_request_with_body(logger, request, "Firdaria request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        result = await run_heavy(
            FirdariaFactory.from_subject,
            subject,
            target_date=request_body.target_date,
            life_cap_years=request_body.life_cap_years,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "firdaria": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)


@router.post("/api/v6/traditional/horary-indicators", response_model=HoraryIndicatorsResponseModel, operation_id="advancedHoraryIndicators")
async def horary_indicators(request_body: HoraryIndicatorsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/traditional/horary-indicators`

    Assemble horary significators and the classical considerations before
    judgment for a question chart: the querent's (1st house) and quesited's
    (7th house) significators via classical rulership, the Ascendant degree
    read from the true Ascendant point (Whole Sign safe), the considerations
    as stable keys, and the chart's mutual receptions.

    **Parameters:**
    - `subject`: Chart cast for the moment of the question.
    - `is_moon_void`: Whether the Moon is void of course, when known from the
      void-of-course search. Omitted: the Moon considerations are skipped.

    **Returns:**
    - `horary_indicators`: Significators, Ascendant degree, considerations,
      mutual receptions.
    """
    log_request_with_body(logger, request, "Horary indicators request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)

        result = await run_heavy(
            HoraryIndicatorsFactory.from_subject,
            subject,
            is_moon_void=request_body.is_moon_void,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "horary_indicators": dump(result),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
