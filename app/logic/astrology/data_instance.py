"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import html
from logging import getLogger
from kerykeion import KrInstance, MakeSvgInstance, RelationshipScore
from pathlib import Path
from logging import getLogger
from .utils import filtrateAndGetDict

logger = getLogger(__name__)


class DataInstanceV2:
    """
    Calculates all the data.
    """

    def __init__(
        self,
        name: str,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        lng,
        lat,
        city,
        tz: str,
        language: str = "IT",
    ):
        self.CURRENT_DIR = Path(__file__).parent
        self.language = language

        self.basic_kr_instance = KrInstance(
            name=html.escape(name),
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lng=lng,
            lat=lat,
            city=html.escape(city),
            tz_str=html.escape(tz),
            geonames_username="g.battaglia",
        )

    def get_birth_data(self):
        user = self.basic_kr_instance
        first_data = filtrateAndGetDict(user)

        return {"data": first_data}

    def get_birth_chart(self):
        user = self.basic_kr_instance
        birth_data = filtrateAndGetDict(user)
        ChartInstance = MakeSvgInstance(
            user,
            chart_type="Natal",
            new_settings_file=self.CURRENT_DIR / "kr.config.json",
        )

        return {
            "chart": ChartInstance.makeTemplate(),
            "data": birth_data,
            "aspects": ChartInstance.aspects_list,
        }

    def get_discepolo_score(
        self,
        name: str,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        lng,
        lat,
        city: str,
        tz: str,
    ):
        """
        Returns compatibility score number according to Ciro Discepolo method.

        Args:
            - name (str): Second subject name
            - year (int): Second subject year
            - month (int): Second subject month
            - day (int): Second subject day
            - hour (int): Second subject hour
            - minute (int): Second subject minute
            - lng (_type_): Second subject longitude
            - lat (_type_): Second subject latitude
            - city (str): Second subject city
            - tz (str): Second subject timezone

        Returns:
            Object: {
                score (int): Compatibility score number
                aspects (list): Aspects list
                data (dict): {
                    first_data (dict): First subject data
                    second_data (dict): Second subject data
                }
            }
        """

        first_kr_instance = self.basic_kr_instance
        second_kr_instance = KrInstance(
            name=html.escape(name),
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lng=lng,
            lat=lat,
            city=html.escape(city),
            tz_str=html.escape(tz),
        )

        discepolo = RelationshipScore(first_kr_instance, second_kr_instance)

        first_data = filtrateAndGetDict(first_kr_instance)
        second_data = filtrateAndGetDict(second_kr_instance)

        return {
            "score": discepolo.score,
            "aspects": discepolo.relevant_default_aspects,
            "data": {"first_data": first_data, "second_data": second_data},
        }

    def get_composite_chart(
        self,
        name: str,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        lng,
        lat,
        city: str,
        tz: str,
    ):
        first_kr_instance = self.basic_kr_instance
        second_kr_instance = KrInstance(
            name=html.escape(name),
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lng=lng,
            lat=lat,
            city=html.escape(city),
            tz_str=html.escape(tz),
        )

        ChartInstance = MakeSvgInstance(
            first_kr_instance,
            chart_type="Composite",
            second_obj=second_kr_instance,
            new_settings_file=self.CURRENT_DIR / "kr.config.json",
        )

        return {
            "chart": ChartInstance.makeTemplate(),
            "data": [filtrateAndGetDict(first_kr_instance), filtrateAndGetDict(second_kr_instance)],
            "aspects": ChartInstance.aspects_list,
        }
