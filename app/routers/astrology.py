"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""


from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from logging import getLogger
from kerykeion import KrInstance

from ..models.requests import SubjectModel, TransitModel
from ..models.responses import AstrologicalDataResponseModel, AstrologicalBirthChartResponseModel
from ..logic.astrology.data_instance import DataInstanceV2
from ..logic.astrology.utils import filtrateAndGetDict
from ..utils.write_response_to_log import get_write_response_to_log
from ..utils.internal_server_error_json_response import InternalServerErrorJsonResponse

write_response_to_log = get_write_response_to_log(getLogger(__name__))

router = APIRouter()


@router.get("/api/v3/now", response_model=AstrologicalDataResponseModel)
async def get_now(request: Request) -> JSONResponse:
    """
    Returns the current astrological data in JSON format.
    """

    write_response_to_log(20, request, "Getting current astrological data")

    try:
        kr_object = KrInstance(
            city="GMT",
            nation="UK",
            lat=51.477928,
            lng=-0.001545,
            tz_str="GMT",
            geonames_username="g.battaglia",
        )

        response_dict = {"status": "OK", "data": filtrateAndGetDict(kr_object)}

        return JSONResponse(content=response_dict, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v3/birth-chart", response_model=AstrologicalBirthChartResponseModel)
async def birth_chart(subject: SubjectModel, request: Request):
    """
    Returns the Birth Chart of a subject in SVG format. Also includes the Birth Chart data and aspects in JSON.
    Parameters to be inserted in the body:

    * `name` - The name of the person to get the Birth Chart for.
    * `year` - The year of birth.
    * `month` - The month of birth.
    * `day` - The day of birth.
    * `hour` - The hour of birth.
    * `minute` - The minute of birth.
    * `latitude` - The latitude of the birth location.
    * `longitude` - The longitude of the birth location.
    * `city` - The name of city of birth.
    * `timezone` - The timezone of the birth location.
    * `language` - The language of the birth chart, currently just English, Italian and Portuguese are available.

    """

    write_response_to_log(20, request, f"Getting birth chart for: {request}")

    try:
        user = DataInstanceV2(
            subject.name,
            subject.year,
            subject.month,
            subject.day,
            subject.hour,
            subject.minute,
            subject.longitude,
            subject.latitude,
            subject.city,
            subject.timezone,
            subject.language,
        )

        object = user.get_birth_chart()
        object["status"] = "OK"

        return JSONResponse(content=object, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v3/birth-data", response_model=AstrologicalDataResponseModel)
async def birth_data(subject: SubjectModel, request: Request) -> JSONResponse:
    """Get the astrological birth data of a subject."""

    write_response_to_log(20, request, f"Getting birth data for: {subject}")

    try:
        user = DataInstanceV2(
            subject.name,
            subject.year,
            subject.month,
            subject.day,
            subject.hour,
            subject.minute,
            subject.longitude,
            subject.latitude,
            subject.city,
            subject.timezone,
        )

        object = user.get_birth_data()
        object["status"] = "OK"

        write_response_to_log(20, request, f"Birth data for {subject} retrieved successfully")

        return JSONResponse(content=object, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)

        return InternalServerErrorJsonResponse


@router.post("/api/v3/composite-chart")
async def composite_chart(first_subject: SubjectModel, second_subject: SubjectModel, request: Request):
    """
    Get the composite chart data of two subjects.
    """
    write_response_to_log(
        20,
        request,
        f"Getting composite chart for: {first_subject} and {second_subject}",
    )

    try:
        user_instance = DataInstanceV2(
            first_subject.name,
            first_subject.year,
            first_subject.month,
            first_subject.day,
            first_subject.hour,
            first_subject.minute,
            first_subject.longitude,
            first_subject.latitude,
            first_subject.city,
            first_subject.timezone,
            first_subject.language,
        )

        object = user_instance.get_composite_chart(
            second_subject.name,
            second_subject.year,
            second_subject.month,
            second_subject.day,
            second_subject.hour,
            second_subject.minute,
            second_subject.longitude,
            second_subject.latitude,
            second_subject.city,
            second_subject.timezone,
        )

        object["status"] = "OK"

        return JSONResponse(content=object, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v3/discepolo-score")
async def discepolo_score(first_subject: SubjectModel, second_subject: SubjectModel, request: Request) -> JSONResponse:
    """
    Get compatibility score number according to Ciro Discepolo method.

    """

    write_response_to_log(20, request, f"Getting composite data for: {first_subject} and {second_subject}")

    try:
        user = DataInstanceV2(
            first_subject.name,
            first_subject.year,
            first_subject.month,
            first_subject.day,
            first_subject.hour,
            first_subject.minute,
            first_subject.longitude,
            first_subject.latitude,
            first_subject.city,
            first_subject.timezone,
            first_subject.language,
        )

        object = user.get_discepolo_score(
            second_subject.name,
            second_subject.year,
            second_subject.month,
            second_subject.day,
            second_subject.hour,
            second_subject.minute,
            second_subject.longitude,
            second_subject.latitude,
            second_subject.city,
            second_subject.timezone,
        )

        object["status"] = "OK"

        return JSONResponse(content=object, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v3/transit-chart")
async def transit_chart(subject: SubjectModel, transit: TransitModel, request: Request):
    """
    Get the transit chart data of a subject.
    """

    write_response_to_log(20, request, f"Getting transit chart for: {subject}")

    return JSONResponse(content={"status": "OK"}, status_code=200)
