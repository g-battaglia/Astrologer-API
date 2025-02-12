# External Libraries
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from logging import getLogger
from kerykeion import AstrologicalSubject, KerykeionChartSVG, SynastryAspects, NatalAspects, RelationshipScoreFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from requests import get as requests_get

# Local
from ..utils.internal_server_error_json_response import InternalServerErrorJsonResponse
from ..utils.write_request_to_log import get_write_request_to_log
from ..types.request_models import (
    BirthDataRequestModel,
    BirthChartRequestModel,
    SynastryChartRequestModel,
    TransitChartRequestModel,
    RelationshipScoreRequestModel,
    SynastryAspectsRequestModel,
    NatalAspectsRequestModel,
)
from ..types.response_models import (
    BirthDataResponseModel,
    BirthChartResponseModel,
    SynastryChartResponseModel,
    RelationshipScoreResponseModel,
    SynastryAspectsResponseModel
)

logger = getLogger(__name__)
write_request_to_log = get_write_request_to_log(logger)

router = APIRouter()


@router.get("/", response_description="Status of the API", response_model=BirthDataResponseModel, include_in_schema=False)
async def status(request: Request) -> JSONResponse:
    """
    Returns the status of the API.
    """

    from ..config.settings import settings

    write_request_to_log(20, request, "API is up and running")
    response_dict = {
        "status": "OK",
        "environment": settings.env_type,
        "debug": settings.debug,
    }

    return JSONResponse(content=response_dict, status_code=200)


@router.get("/api/v4/now", response_description="Current astrological data", response_model=BirthDataResponseModel)
async def get_now(request: Request) -> JSONResponse:
    """
    Retrieve astrological data for the current moment.
    """

    # Get current UTC time from the time API
    write_request_to_log(20, request, "Getting current astrological data")

    try:
        # On some Cloud providers, the time is not set correctly, so we need to get the current UTC time from the time API
        logger.debug("Getting current UTC time from the time API")
        datetime_dict = requests_get("https://timeapi.io/api/Time/current/zone?timeZone=UTC").json()
        logger.debug(f"Current UTC time: {datetime_dict}")

        today_subject = AstrologicalSubject(
            city="GMT",
            nation="UK",
            lat=51.477928,
            lng=-0.001545,
            tz_str="GMT",
            year=datetime_dict["year"],
            month=datetime_dict["month"],
            day=datetime_dict["day"],
            hour=datetime_dict["hour"],
            minute=datetime_dict["minute"],
            online=False,
        )

        response_dict = {"status": "OK", "data": today_subject.model().model_dump()}

        return JSONResponse(content=response_dict, status_code=200)

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/birth-data", response_description="Birth data", response_model=BirthDataResponseModel)
async def birth_data(birth_data_request: BirthDataRequestModel, request: Request):
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    subject = birth_data_request.subject

    try:
        astrological_subject = AstrologicalSubject(
            name=subject.name,
            year=subject.year,
            month=subject.month,
            day=subject.day,
            hour=subject.hour,
            minute=subject.minute,
            city=subject.city,
            nation=subject.nation,
            lat=subject.latitude,
            lng=subject.longitude,
            tz_str=subject.timezone,
            zodiac_type=subject.zodiac_type, # type: ignore
            sidereal_mode=subject.sidereal_mode,
            houses_system_identifier=subject.houses_system_identifier, # type: ignore
            perspective_type=subject.perspective_type, # type: ignore
            online=False,
        )

        data = astrological_subject.model().model_dump()

        response_dict = {"status": "OK", "data": data}

        return JSONResponse(content=response_dict, status_code=200)

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/birth-chart", response_description="Birth chart", response_model=BirthChartResponseModel)
async def birth_chart(request_body: BirthChartRequestModel, request: Request):
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    subject = request_body.subject

    try:
        astrological_subject = AstrologicalSubject(
            name=subject.name,
            year=subject.year,
            month=subject.month,
            day=subject.day,
            hour=subject.hour,
            minute=subject.minute,
            city=subject.city,
            nation=subject.nation,
            lat=subject.latitude,
            lng=subject.longitude,
            tz_str=subject.timezone,
            zodiac_type=subject.zodiac_type, # type: ignore
            sidereal_mode=subject.sidereal_mode,
            houses_system_identifier=subject.houses_system_identifier, # type: ignore
            perspective_type=subject.perspective_type, # type: ignore
            online=False,
        )

        data = astrological_subject.model().model_dump()

        kerykeion_chart = KerykeionChartSVG(
            astrological_subject,
            theme=request_body.theme,
            chart_language=request_body.language or "EN",
            active_points=request_body.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=request_body.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        )

        if request_body.wheel_only:
            svg = kerykeion_chart.makeWheelOnlyTemplate(minify=True)
        else:
            svg = kerykeion_chart.makeTemplate(minify=True)

        return JSONResponse(
            content={
                "status": "OK",
                "chart": svg,
                "data": data,
                "aspects": [aspect.model_dump() for aspect in kerykeion_chart.aspects_list]
            },
            status_code=200,
        )

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/synastry-chart", response_description="Synastry data")
async def synastry_chart(synastry_chart_request: SynastryChartRequestModel, request: Request):
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    first_subject = synastry_chart_request.first_subject
    second_subject = synastry_chart_request.second_subject

    try:
        first_astrological_subject = AstrologicalSubject(
            name=first_subject.name,
            year=first_subject.year,
            month=first_subject.month,
            day=first_subject.day,
            hour=first_subject.hour,
            minute=first_subject.minute,
            city=first_subject.city,
            nation=first_subject.nation,
            lat=first_subject.latitude,
            lng=first_subject.longitude,
            tz_str=first_subject.timezone,
            zodiac_type=first_subject.zodiac_type, # type: ignore
            sidereal_mode=first_subject.sidereal_mode,
            houses_system_identifier=first_subject.houses_system_identifier, # type: ignore
            perspective_type=first_subject.perspective_type, # type: ignore
            online=False,
        )

        second_astrological_subject = AstrologicalSubject(
            name=second_subject.name,
            year=second_subject.year,
            month=second_subject.month,
            day=second_subject.day,
            hour=second_subject.hour,
            minute=second_subject.minute,
            city=second_subject.city,
            nation=second_subject.nation,
            lat=second_subject.latitude,
            lng=second_subject.longitude,
            tz_str=second_subject.timezone,
            zodiac_type=second_subject.zodiac_type, # type: ignore
            sidereal_mode=second_subject.sidereal_mode,
            houses_system_identifier=second_subject.houses_system_identifier, # type: ignore
            perspective_type=second_subject.perspective_type, # type: ignore
            online=False,
        )

        kerykeion_chart = KerykeionChartSVG(
            first_astrological_subject,
            second_obj=second_astrological_subject,
            chart_type="Synastry",
            theme=synastry_chart_request.theme,
            chart_language=synastry_chart_request.language or "EN",
            active_points=synastry_chart_request.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=synastry_chart_request.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        )

        if synastry_chart_request.wheel_only:
            svg = kerykeion_chart.makeWheelOnlyTemplate(minify=True)
        else:
            svg = kerykeion_chart.makeTemplate(minify=True)

        return JSONResponse(
            content={
                "status": "OK",
                "chart": svg,
                "aspects": [aspect.model_dump() for aspect in kerykeion_chart.aspects_list],
                "data": {
                    "first_subject": first_astrological_subject.model().model_dump(),
                    "second_subject": second_astrological_subject.model().model_dump(),
                },
            },
            status_code=200,
        )

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/transit-chart", response_description="Transit data", response_model=SynastryChartResponseModel)
async def transit_chart(transit_chart_request: TransitChartRequestModel, request: Request):
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    first_subject = transit_chart_request.first_subject
    second_subject = transit_chart_request.transit_subject

    try:
        first_astrological_subject = AstrologicalSubject(
            name=first_subject.name,
            year=first_subject.year,
            month=first_subject.month,
            day=first_subject.day,
            hour=first_subject.hour,
            minute=first_subject.minute,
            city=first_subject.city,
            nation=first_subject.nation,
            lat=first_subject.latitude,
            lng=first_subject.longitude,
            tz_str=first_subject.timezone,
            zodiac_type=first_subject.zodiac_type, # type: ignore
            sidereal_mode=first_subject.sidereal_mode,
            houses_system_identifier=first_subject.houses_system_identifier, # type: ignore
            perspective_type=first_subject.perspective_type, # type: ignore
            online=False,
        )

        second_astrological_subject = AstrologicalSubject(
            name="Transit",
            year=second_subject.year,
            month=second_subject.month,
            day=second_subject.day,
            hour=second_subject.hour,
            minute=second_subject.minute,
            city=second_subject.city,
            nation=second_subject.nation,
            lat=second_subject.latitude,
            lng=second_subject.longitude,
            tz_str=second_subject.timezone,
            zodiac_type=first_astrological_subject.zodiac_type, # type: ignore
            sidereal_mode=first_subject.sidereal_mode,
            houses_system_identifier=first_subject.houses_system_identifier, # type: ignore
            perspective_type=first_subject.perspective_type, # type: ignore
            online=False,
        )

        kerykeion_chart = KerykeionChartSVG(
            first_astrological_subject,
            second_obj=second_astrological_subject,
            chart_type="Transit",
            theme=transit_chart_request.theme,
            chart_language=transit_chart_request.language or "EN",
            active_points=transit_chart_request.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=transit_chart_request.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        )

        if transit_chart_request.wheel_only:
            svg = kerykeion_chart.makeWheelOnlyTemplate(minify=True)
        else:
            svg = kerykeion_chart.makeTemplate(minify=True)

        return JSONResponse(
            content={
                "status": "OK",
                "chart": svg,
                "aspects": [aspect.model_dump() for aspect in kerykeion_chart.aspects_list],
                "data": {
                    "subject": first_astrological_subject.model().model_dump(),
                    "transit": second_astrological_subject.model().model_dump(),
                },
            },
            status_code=200,
        )

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/synastry-aspects-data", response_description="Synastry aspects data", response_model=SynastryAspectsResponseModel)
async def synastry_aspects_data(aspects_request_content: SynastryAspectsRequestModel, request: Request) -> JSONResponse:
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    first_subject = aspects_request_content.first_subject
    second_subject = aspects_request_content.second_subject

    try:
        first_astrological_subject = AstrologicalSubject(
            name=first_subject.name,
            year=first_subject.year,
            month=first_subject.month,
            day=first_subject.day,
            hour=first_subject.hour,
            minute=first_subject.minute,
            city=first_subject.city,
            nation=first_subject.nation,
            lat=first_subject.latitude,
            lng=first_subject.longitude,
            tz_str=first_subject.timezone,
            zodiac_type=first_subject.zodiac_type, # type: ignore
            sidereal_mode=first_subject.sidereal_mode,
            houses_system_identifier=first_subject.houses_system_identifier, # type: ignore
            perspective_type=first_subject.perspective_type, # type: ignore
            online=False,
        )

        second_astrological_subject = AstrologicalSubject(
            name=second_subject.name,
            year=second_subject.year,
            month=second_subject.month,
            day=second_subject.day,
            hour=second_subject.hour,
            minute=second_subject.minute,
            city=second_subject.city,
            nation=second_subject.nation,
            lat=second_subject.latitude,
            lng=second_subject.longitude,
            tz_str=second_subject.timezone,
            zodiac_type=second_subject.zodiac_type, # type: ignore
            sidereal_mode=second_subject.sidereal_mode,
            houses_system_identifier=second_subject.houses_system_identifier, # type: ignore
            perspective_type=second_subject.perspective_type, # type: ignore
            online=False,
        )

        aspects = SynastryAspects(
            first_astrological_subject,
            second_astrological_subject,
            active_points=aspects_request_content.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=aspects_request_content.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        ).relevant_aspects

        return JSONResponse(
            content={
                "status": "OK",
                "data": {
                    "first_subject": first_astrological_subject.model().model_dump(),
                    "second_subject": second_astrological_subject.model().model_dump(),
                },
                "aspects": [aspect.model_dump() for aspect in aspects],
            },
            status_code=200,
        )

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/natal-aspects-data", response_description="Birth aspects data", response_model=SynastryAspectsResponseModel)
async def natal_aspects_data(aspects_request_content: NatalAspectsRequestModel, request: Request) -> JSONResponse:
    write_request_to_log(20, request, f"Getting birth chart for: {request}")

    subject = aspects_request_content.subject

    try:
        first_astrological_subject = AstrologicalSubject(
            name=subject.name,
            year=subject.year,
            month=subject.month,
            day=subject.day,
            hour=subject.hour,
            minute=subject.minute,
            city=subject.city,
            nation=subject.nation,
            lat=subject.latitude,
            lng=subject.longitude,
            tz_str=subject.timezone,
            zodiac_type=subject.zodiac_type, # type: ignore
            sidereal_mode=subject.sidereal_mode,
            houses_system_identifier=subject.houses_system_identifier, # type: ignore
            perspective_type=subject.perspective_type, # type: ignore
            online=False,
        )

        aspects = NatalAspects(
            first_astrological_subject,
            active_points=aspects_request_content.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=aspects_request_content.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        ).relevant_aspects

        return JSONResponse(
            content={
                "status": "OK",
                "data": {"subject": first_astrological_subject.model().model_dump()},
                "aspects": [aspect.model_dump() for aspect in aspects],
            },
            status_code=200,
        )

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/relationship-score", response_description="Relationship score", response_model=RelationshipScoreResponseModel)
async def relationship_score(relationship_score_request: RelationshipScoreRequestModel, request: Request) -> JSONResponse:
    """
    Calculates the relevance of the relationship between two subjects using the Ciro Discepolo method.

    Results:
        - 0 to 5: Minimal relationship
        - 5 to 10: Medium relationship
        - 10 to 15: Important relationship
        - 15 to 20: Very important relationship
        - 20 to 35: Exceptional relationship
        - 30 and above: Rare Exceptional relationship

    More details: https://www-cirodiscepolo-it.translate.goog/Articoli/Discepoloele.htm?_x_tr_sl=it&_x_tr_tl=en&_x_tr_hl=it&_x_tr_pto=wapp
    """

    first_subject = relationship_score_request.first_subject
    second_subject = relationship_score_request.second_subject

    write_request_to_log(20, request, f"Getting composite data for: {first_subject} and {second_subject}")

    try:
        first_astrological_subject = AstrologicalSubject(
            name=first_subject.name,
            year=first_subject.year,
            month=first_subject.month,
            day=first_subject.day,
            hour=first_subject.hour,
            minute=first_subject.minute,
            city=first_subject.city,
            nation=first_subject.nation,
            lat=first_subject.latitude,
            lng=first_subject.longitude,
            tz_str=first_subject.timezone,
            zodiac_type=first_subject.zodiac_type, # type: ignore
            sidereal_mode=first_subject.sidereal_mode,
            houses_system_identifier=first_subject.houses_system_identifier, # type: ignore
            perspective_type=first_subject.perspective_type, # type: ignore
            online=False,
        )

        second_astrological_subject = AstrologicalSubject(
            name=second_subject.name,
            year=second_subject.year,
            month=second_subject.month,
            day=second_subject.day,
            hour=second_subject.hour,
            minute=second_subject.minute,
            city=second_subject.city,
            nation=second_subject.nation,
            lat=second_subject.latitude,
            lng=second_subject.longitude,
            tz_str=second_subject.timezone,
            zodiac_type=second_subject.zodiac_type, # type: ignore
            sidereal_mode=second_subject.sidereal_mode,
            houses_system_identifier=second_subject.houses_system_identifier, # type: ignore
            perspective_type=second_subject.perspective_type, # type: ignore
            online=False,
        )

        score_factory = RelationshipScoreFactory(first_astrological_subject, second_astrological_subject)
        score_model = score_factory.get_relationship_score()

        response_content = {
            "status": "OK",
            "score": score_model.score_value,
            "score_description": score_model.score_description,
            "is_destiny_sign": score_model.is_destiny_sign,
            "aspects": [aspect.model_dump() for aspect in score_model.aspects],
            "data": {
                "first_subject": first_astrological_subject.model().model_dump(),
                "second_subject": second_astrological_subject.model().model_dump(),
            },
        }

        return JSONResponse(content=response_content, status_code=200)

    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse
