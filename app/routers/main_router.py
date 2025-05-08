# External Libraries
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from logging import getLogger
from kerykeion import (
    AstrologicalSubject, 
    KerykeionChartSVG, 
    SynastryAspects, 
    NatalAspects, 
    RelationshipScoreFactory, 
    CompositeSubjectFactory
)
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS

# Local
from ..utils.internal_server_error_json_response import InternalServerErrorJsonResponse
from ..utils.get_time_from_google import get_time_from_google
from ..utils.write_request_to_log import get_write_request_to_log
from ..types.request_models import (
    BirthDataRequestModel,
    BirthChartRequestModel,
    SynastryChartRequestModel,
    TransitChartRequestModel,
    RelationshipScoreRequestModel,
    SynastryAspectsRequestModel,
    NatalAspectsRequestModel,
    CompositeChartRequestModel
)
from ..types.response_models import (
    BirthDataResponseModel,
    BirthChartResponseModel,
    SynastryChartResponseModel,
    RelationshipScoreResponseModel,
    SynastryAspectsResponseModel,
    CompositeChartResponseModel,
    CompositeAspectsResponseModel,
    TransitAspectsResponseModel,
    TransitChartResponseModel
)

logger = getLogger(__name__)
write_request_to_log = get_write_request_to_log(logger)

router = APIRouter()

GEONAMES_ERROR_MESSAGE = "City/Nation name error or invalid GeoNames username. Please check your username or city name and try again. You can create a free username here: https://www.geonames.org/login/. If you want to bypass the usage of GeoNames, please remove the geonames_username field from the request. Note: The nation field should be the country code (e.g. US, UK, FR, DE, etc.)."

@router.get("/api/v4/health", response_description="Health check", include_in_schema=False)
async def health(request: Request) -> JSONResponse:
    """
    Health check endpoint.
    """

    write_request_to_log(20, request, "Health check")

    return JSONResponse(content={"status": "OK"}, status_code=200)


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
    
    logger.debug("Getting current UTC time from the time API")
    try:
        utc_datetime = get_time_from_google()
        datetime_dict = {
            "year": utc_datetime.year, # type: ignore
            "month": utc_datetime.month, # type: ignore
            "day": utc_datetime.day, # type: ignore
            "hour": utc_datetime.hour, # type: ignore
            "minute": utc_datetime.minute, # type: ignore
            "second": utc_datetime.second, # type: ignore
        }
    except Exception as e:
        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse
    logger.debug(f"Current UTC time: {datetime_dict}")

    try:
        # On some Cloud providers, the time is not set correctly, so we need to get the current UTC time from the time API
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
    """
    Retrieve astrological data for a specific birth date. Does not include the chart nor the aspects.
    """

    write_request_to_log(20, request, f"Birth data request")

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
            geonames_username=subject.geonames_username,
            online=True if subject.geonames_username else False,
        )

        data = astrological_subject.model().model_dump()

        response_dict = {"status": "OK", "data": data}

        return JSONResponse(content=response_dict, status_code=200)

    except Exception as e:
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/birth-chart", response_description="Birth chart", response_model=BirthChartResponseModel)
async def birth_chart(request_body: BirthChartRequestModel, request: Request):
    """
    Retrieve an astrological birth chart for a specific birth date. Includes the data for the subject and the aspects.
    """

    write_request_to_log(20, request, f"Birth chart request")

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
            geonames_username=subject.geonames_username,
            online=True if subject.geonames_username else False,
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
        # If error contains "wrong username"
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/synastry-chart", response_description="Synastry data", response_model=SynastryChartResponseModel)
async def synastry_chart(synastry_chart_request: SynastryChartRequestModel, request: Request):
    """
    Retrieve a synastry chart between two subjects. Includes the data for the subjects and the aspects.
    """

    write_request_to_log(20, request, f"Synastry chart request")

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
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
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/transit-chart", response_description="Transit data", response_model=TransitChartResponseModel)
async def transit_chart(transit_chart_request: TransitChartRequestModel, request: Request):
    """
    Retrieve a transit chart for a specific subject. Includes the data for the subject and the aspects.
    """

    write_request_to_log(20, request, f"Transit chart request")

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
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
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/transit-aspects-data", response_description="Transit aspects data", response_model=TransitAspectsResponseModel)
async def transit_aspects_data(transit_chart_request: TransitChartRequestModel, request: Request) -> JSONResponse:
    """
    Retrieve transit aspects and data for a specific subject. Does not include the chart.
    """

    write_request_to_log(20, request, f"Transit aspects data request")

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
        )

        aspects = SynastryAspects(
            first_astrological_subject,
            second_astrological_subject,
            active_points=transit_chart_request.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=transit_chart_request.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        ).relevant_aspects

        return JSONResponse(
            content={
                "status": "OK",
                "data": {
                    "subject": first_astrological_subject.model().model_dump(),
                    "transit": second_astrological_subject.model().model_dump(),
                },
                "aspects": [aspect.model_dump() for aspect in aspects],
            },
            status_code=200,
        )

    except Exception as e:
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/synastry-aspects-data", response_description="Synastry aspects data", response_model=SynastryAspectsResponseModel)
async def synastry_aspects_data(aspects_request_content: SynastryAspectsRequestModel, request: Request) -> JSONResponse:
    """
    Retrieve synastry aspects between two subjects. Does not include the chart.
    """

    write_request_to_log(20, request, f"Synastry aspects data request")

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
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
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/natal-aspects-data", response_description="Birth aspects data", response_model=SynastryAspectsResponseModel)
async def natal_aspects_data(aspects_request_content: NatalAspectsRequestModel, request: Request) -> JSONResponse:
    """
    Retrieve natal aspects and data for a specific subject. Does not include the chart.
    """

    write_request_to_log(20, request, f"Natal aspects data request")

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
            geonames_username=subject.geonames_username,
            online=True if subject.geonames_username else False,
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
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
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
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/composite-chart", response_description="Composite data", response_model=CompositeChartResponseModel)
async def composite_chart(composite_chart_request: CompositeChartRequestModel, request: Request) -> JSONResponse:
    """
    Retrieve a composite chart between two subjects. Includes the data for the subjects and the aspects.
    The method used is the midpoint method.
    """

    first_subject = composite_chart_request.first_subject
    second_subject = composite_chart_request.second_subject

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
        )

        composite_factory = CompositeSubjectFactory(first_astrological_subject, second_astrological_subject)
        composite_subject = composite_factory.get_midpoint_composite_subject_model()

        kerykeion_chart = KerykeionChartSVG(
            composite_subject,
            chart_type="Composite",
            theme=composite_chart_request.theme
        )

        if composite_chart_request.wheel_only:
            svg = kerykeion_chart.makeWheelOnlyTemplate(minify=True)
        else:
            svg = kerykeion_chart.makeTemplate(minify=True)

        composite_subject_dict = composite_subject.model_dump()
        for key in ["first_subject", "second_subject"]:
            if key in composite_subject_dict:
                composite_subject_dict.pop(key)

        return JSONResponse(
            content={
                "status": "OK",
                "chart": svg,
                "aspects": [aspect.model_dump() for aspect in kerykeion_chart.aspects_list],
                "data": {
                    "composite_subject": composite_subject_dict,
                    "first_subject": first_astrological_subject.model().model_dump(),
                    "second_subject": second_astrological_subject.model().model_dump(),
                },
            },
            status_code=200,
        )

    except Exception as e:
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse


@router.post("/api/v4/composite-aspects-data", response_description="Composite aspects data", response_model=CompositeAspectsResponseModel)
async def composite_aspects_data(composite_chart_request: CompositeChartRequestModel, request: Request) -> JSONResponse:
    """
    Retrieves the data and the aspects for a composite chart between two subjects. Does not include the chart.
    """

    first_subject = composite_chart_request.first_subject
    second_subject = composite_chart_request.second_subject

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
            geonames_username=first_subject.geonames_username,
            online=True if first_subject.geonames_username else False,
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
            geonames_username=second_subject.geonames_username,
            online=True if second_subject.geonames_username else False,
        )

        composite_factory = CompositeSubjectFactory(first_astrological_subject, second_astrological_subject)
        composite_data = composite_factory.get_midpoint_composite_subject_model()
        aspects = NatalAspects(
            composite_data,
            active_points=composite_chart_request.active_points or DEFAULT_ACTIVE_POINTS,
            active_aspects=composite_chart_request.active_aspects or DEFAULT_ACTIVE_ASPECTS,
        ).relevant_aspects

        composite_subject_dict = composite_data.model_dump()
        for key in ["first_subject", "second_subject"]:
            if key in composite_subject_dict:
                composite_subject_dict.pop(key)

        return JSONResponse(
            content={
                "status": "OK",
                "data": {
                    "composite_subject": composite_subject_dict,
                    "first_subject": first_astrological_subject.model().model_dump(),
                    "second_subject": second_astrological_subject.model().model_dump(),
                },
                "aspects": [aspect.model_dump() for aspect in aspects],
            },
            status_code=200,
        )

    except Exception as e:
        if "data found for this city" in str(e):
            write_request_to_log(40, request, e)
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": GEONAMES_ERROR_MESSAGE,
                },
                status_code=400,
            )

        write_request_to_log(40, request, e)
        return InternalServerErrorJsonResponse