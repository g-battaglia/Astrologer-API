"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from logging import getLogger
import requests
from requests_cache import CachedSession

logger = getLogger(__name__)


class Geonames:
    """
    Get geo data from city name initial letters and country code.
    """

    def __init__(
        self,
        city_letters: str,
        country_code: str,
        geonames_username: str = "g.battaglia",
    ):
        self.city_letters = city_letters
        self.country_code = country_code
        self.geonames_username = geonames_username
        self.base_url = "http://api.geonames.org/searchJSON"
        self.session = CachedSession(cache_name="cache/geonames_cache", backend="sqlite", expire_after=86400)

    def __request_geoname_data(self) -> list:
        """
        Do the request to the geonames api and returns all the data.
        """
        params = {
            "name_startsWith": self.city_letters,
            "country": self.country_code,
            "username": self.geonames_username,
            "maxRows": 10,
            "featureClass": "P",
        }

        prepared_request = requests.Request("GET", self.base_url, params=params).prepare()
        logger.info(f"Requesting data from geonames api:\n{prepared_request.url}")

        try:
            response = self.session.send(prepared_request)
            data = response.json()

        except Exception as e:
            logger.error(f"Error: {e}")

            return []

        logger.info(f"Request Successful: {response.status_code} Used cache: {response.from_cache}")  # type: ignore

        return data.get("geonames")

    def get_serialized_city_data(self) -> list[dict[str, str]]:
        """
        Get the city data from the geonames api and returns
        the final object serialized with the usefull data.
        """
        data = self.__request_geoname_data()

        if not data:
            return []

        serialized_objects_list = []

        for city in data:
            city_obj = {
                "name": city.get("name"),
                "lat": city.get("lat"),
                "lng": city.get("lng"),
                "country": city.get("countryName"),
                "country_code": city.get("countryCode"),
                "admin_name": city.get("adminCode1"),
                "name_located": f"{city.get('name')}, {city.get('adminName1')}",
            }
            serialized_objects_list.append(city_obj)

        return serialized_objects_list
