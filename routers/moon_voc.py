"""
Void-of-course Moon endpoint.

Thin REST wrapper over kerykeion's :class:`VoidOfCourseMoonFactory`: the whole
algorithm (sign ingress, exact-aspect search, void window) lives in kerykeion;
this handler only adapts the request and serialises the resulting model.
"""

from logging import getLogger
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion import VoidOfCourseMoonFactory

from ..types.request_models import MoonVocRequestModel, MoonVocWindowsRequestModel
from ..types.response_models import MoonVocResponseModel, MoonVocWindowsResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import handle_exception, run_heavy
from ..utils.astronomy_payloads import _moon_voc_payload, _window_payload

logger = getLogger(__name__)

router = APIRouter()


@router.post("/api/v6/moon/void-of-course", response_model=MoonVocResponseModel, operation_id="moonVoc")
async def moon_voc(request_body: MoonVocRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/moon/void-of-course`

    Void-of-course Moon for a moment, computed by kerykeion's
    ``VoidOfCourseMoonFactory``. The Moon is *void of course* once it has perfected
    its last exact Ptolemaic aspect (conjunction, sextile, square, trine,
    opposition) to a traditional planet (Sun, Mercury, Venus, Mars, Jupiter,
    Saturn) while in its current sign, and stays void until it ingresses the next
    sign. The result is geocentric, so no location is required.

    **Returns:** `status` + `moon_voc` { is_void, moon_sign, next_sign, ingress,
    void_start, void_end, last_aspect, next_aspect } (signs are three-letter codes).
    """
    log_request_with_body(logger, request, "Moon void-of-course request", request_body.model_dump_json())
    try:
        model = await run_heavy(
            VoidOfCourseMoonFactory.from_datetime,
            request_body.year,
            request_body.month,
            request_body.day,
            request_body.hour,
            request_body.minute,
            tz_str=request_body.timezone,
            zodiac_type=request_body.zodiac_type,
            sidereal_mode=request_body.sidereal_mode,
        )
        tz = ZoneInfo(request_body.timezone)
        return JSONResponse(content=_moon_voc_payload(model, tz), status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)


@router.post("/api/v6/moon/void-of-course/windows", response_model=MoonVocWindowsResponseModel, operation_id="advancedMoonVocWindows")
async def moon_voc_windows(request_body: MoonVocWindowsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/moon/void-of-course/windows`

    Every void-of-course Moon window intersecting a date range, computed by
    kerykeion's ``VoidOfCourseMoonFactory.from_iso_range``. Each window runs from
    the Moon's last exact Ptolemaic aspect in a sign to its ingress into the next
    sign (~13-14 windows per month). Windows are **unclipped**: the first may
    start before `start_date` and the last may end after `end_date`.

    **Parameters:**
    - `start_date`, `end_date`: ISO date(time) range (treated as UTC, max ~1 year).
    - `timezone`: Optional IANA zone — adds `*_local` ISO strings to each window.
    - `zodiac_type`, `sidereal_mode`: Zodiac (sign boundaries shift when sidereal).

    **Returns:** `status` + `windows[]` { moon_sign, next_sign, void_start(_local),
    void_end(_local), duration_minutes, last_aspect }.
    """
    log_request_with_body(logger, request, "Moon VoC windows request", request_body.model_dump_json())
    try:
        result = await run_heavy(
            VoidOfCourseMoonFactory.from_iso_range,
            request_body.start_date,
            request_body.end_date,
            zodiac_type=request_body.zodiac_type,
            sidereal_mode=request_body.sidereal_mode,
        )
        tz = ZoneInfo(request_body.timezone) if request_body.timezone else None
        return JSONResponse(
            content={
                "status": "OK",
                "windows": [_window_payload(w, tz) for w in result.windows],
            },
            status_code=200,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
