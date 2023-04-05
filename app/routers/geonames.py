"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""


from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from logging import getLogger

from ..models.requests import GeoCity
from ..logic.geonames import Geonames
from ..utils.internal_server_error_json_response import InternalServerErrorJsonResponse
from ..utils.write_response_to_log import get_write_response_to_log


write_response_to_log = get_write_response_to_log(getLogger(__name__))

router = APIRouter()


@router.post("/api/v1/city-data")
async def get_city_data(CityInitial: GeoCity, request: Request):
    """
    Geonames utility to get the city data from the initial letters and country code.
    """
    try:
        write_response_to_log(20, request, "Getting city data")

        geoname = Geonames(CityInitial.city, CityInitial.country, "g.battaglia")
        city_list = geoname.get_serialized_city_data()

        if not city_list:
            return JSONResponse(
                content={"error": "No data found, maybe the city name or contry code is not correct."},
                status_code=404,
            )

        return JSONResponse(content={"data": city_list}, status_code=200)

    except Exception as e:
        write_response_to_log(40, request, e)
        return InternalServerErrorJsonResponse
