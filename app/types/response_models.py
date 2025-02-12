from pydantic import BaseModel, Field

from kerykeion.kr_types import LunarPhaseModel, AstrologicalSubjectModel
from typing import Optional


class AspectModel(BaseModel):
    p1_name: str = Field(description="The name of the first planet.")
    p1_abs_pos: float = Field(description="The absolute position of the first planet.")
    p2_name: str = Field(description="The name of the second planet.")
    p2_abs_pos: float = Field(description="The absolute position of the second planet.")
    aspect: str = Field(description="The aspect between the two planets.")
    orbit: float = Field(description="The orbit between the two planets.")
    aspect_degrees: float = Field(description="The degrees of the aspect.")
    diff: float = Field(description="The difference between the two planets.")
    p1: int = Field(description="The id of the first planet.")
    p2: int = Field(description="The id of the second planet.")


class PlanetModel(BaseModel):
    name: str = Field(description="The name of the planet.")
    quality: str = Field(description="The quality of the planet.")
    element: str = Field(description="The element of the planet.")
    sign: str = Field(description="The sign in which the planet is located.")
    sign_num: int = Field(description="The number of the sign in which the planet is located.")
    position: float = Field(description="The position of the planet inside the sign.")
    abs_pos: float = Field(description="The absolute position of the planet in the 360 degrees circle of the zodiac.")
    emoji: str = Field(description="The emoji of the planet.")
    point_type: str = Field(description="The type of the point.")
    house: Optional[str] = Field(description="The house in which the planet is located.")
    retrograde: Optional[bool] = Field(default=None, description="The retrograde status of the planet.")


class BirthDataModel(BaseModel):
    # Data
    name: str = Field(description="The name of the subject.")
    year: int = Field(description="Year of birth.")
    month: int = Field(description="Month of birth.")
    day: int = Field(description="Day of birth.")
    hour: int = Field(description="Hour of birth.")
    minute: int = Field(description="Minute of birth.")
    city: str = Field(description="City of birth.")
    nation: str = Field(description="Nation of birth.")
    lng: float = Field(description="Longitude of birth.")
    lat: float = Field(description="Latitude of birth.")
    tz_str: str = Field(description="Timezone of birth.")
    zodiac_type: str = Field(description="The type of zodiac used.")
    local_time: str = Field(description="The local time of birth.")
    utc_time: str = Field(description="The UTC time of birth.")
    julian_day: float = Field(description="The Julian day of birth.")

    # Planets
    sun: PlanetModel = Field(description="The data of the Sun.")
    moon: PlanetModel = Field(description="The data of the Moon.")
    mercury: PlanetModel = Field(description="The data of Mercury.")
    venus: PlanetModel = Field(description="The data of Venus.")
    mars: PlanetModel = Field(description="The data of Mars.")
    jupiter: PlanetModel = Field(description="The data of Jupiter.")
    saturn: PlanetModel = Field(description="The data of Saturn.")
    uranus: PlanetModel = Field(description="The data of Uranus.")
    neptune: PlanetModel = Field(description="The data of Neptune.")
    pluto: PlanetModel = Field(description="The data of Pluto.")
    chiron: PlanetModel = Field(description="The data of Chiron.")

    # Houses
    first_house: PlanetModel = Field(description="The data of the first house.")
    second_house: PlanetModel = Field(description="The data of the second house.")
    third_house: PlanetModel = Field(description="The data of the third house.")
    fourth_house: PlanetModel = Field(description="The data of the fourth house.")
    fifth_house: PlanetModel = Field(description="The data of the fifth house.")
    sixth_house: PlanetModel = Field(description="The data of the sixth house.")
    seventh_house: PlanetModel = Field(description="The data of the seventh house.")
    eighth_house: PlanetModel = Field(description="The data of the eighth house.")
    ninth_house: PlanetModel = Field(description="The data of the ninth house.")
    tenth_house: PlanetModel = Field(description="The data of the tenth house.")
    eleventh_house: PlanetModel = Field(description="The data of the eleventh house.")
    twelfth_house: PlanetModel = Field(description="The data of the twelfth house.")

    # Nodes
    mean_node: PlanetModel = Field(description="The data of the mean node.")
    true_node: PlanetModel = Field(description="The data of the true node.")

    # Lunar Phase
    lunar_phase: Optional[LunarPhaseModel]


class BirthDataResponseModel(BaseModel):
    status: str = Field(description="The status of the response.")
    data: BirthDataModel = Field(description="The data of the subject.")


class BirthChartResponseModel(BaseModel):
    status: str = Field(description="The status of the response.")
    data: BirthDataModel = Field(description="The data of the subject.")
    chart: str = Field(description="The SVG chart of the birth chart.")
    aspects: list[AspectModel] = Field(description="The aspects of the birth chart.")


class DoubleDataModel(BaseModel):
    first_subject: AstrologicalSubjectModel = Field(description="The data of the first subject.")
    second_subject: AstrologicalSubjectModel = Field(description="The data of the second subject.")


class SynastryChartResponseModel(BaseModel):
    status: str = Field(description="The status of the response.")
    data: DoubleDataModel = Field(description="The data of the two subjects.")
    chart: str = Field(description="The SVG chart of the synastry.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects.")


class RelationshipScoreResponseModel(BaseModel):
    status: str = Field(description="The status of the response.")
    data: DoubleDataModel = Field(description="The data of the two subjects.")
    score: float = Field(description="The relationship score between the two subjects.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects. In the Kerykeion library is referred as 'relevant_aspects'.")
    is_destiny_sign: bool = Field(description="If the two sings are reciprocally destiny signs.")


class SynastryAspectsResponseModel(BaseModel):
    """
    The response model for the Aspects endpoint.
    """

    status: str = Field(description="The status of the response.")
    data: DoubleDataModel = Field(description="The data of the two subjects.")
    aspects: list[AspectModel] = Field(description="A list with the aspects between the two subjects.")
