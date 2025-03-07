from pydantic import BaseModel, Field

from kerykeion.kr_types import LunarPhaseModel, AstrologicalSubjectModel, CompositeSubjectModel
from kerykeion.kr_types import Quality, Element, Sign, Houses, Planet, AxialCusps, AspectName, SignsEmoji, SignNumbers, PointType, ZodiacType
from typing import Optional


class AspectModel(BaseModel):
    """
    The model for the aspects, similar to the one in the Kerykeion library.
    """
    p1_name: Planet | AxialCusps = Field(description="The name of the first planet.")
    p1_abs_pos: float = Field(description="The absolute position of the first planet.")
    p2_name: Planet | AxialCusps = Field(description="The name of the second planet.")
    p2_abs_pos: float = Field(description="The absolute position of the second planet.")
    aspect: AspectName = Field(description="The aspect between the two planets.")
    orbit: float = Field(description="The orbit between the two planets.")
    aspect_degrees: float = Field(description="The degrees of the aspect.")
    diff: float = Field(description="The difference between the two planets.")
    p1: int = Field(description="The id of the first planet.")
    p2: int = Field(description="The id of the second planet.")


class PlanetModel(BaseModel):
    """
    The model for the planets, similar to the one in the Kerykeion library.
    """

    name: Planet | AxialCusps = Field(description="The name of the planet.")
    quality: Quality = Field(description="The quality of the planet.")
    element: Element = Field(description="The element of the planet.")
    sign: Sign = Field(description="The sign in which the planet is located.")
    sign_num: SignNumbers = Field(description="The number of the sign in which the planet is located.")
    position: float = Field(description="The position of the planet inside the sign.")
    abs_pos: float = Field(description="The absolute position of the planet in the 360 degrees circle of the zodiac.")
    emoji: SignsEmoji = Field(description="The emoji of the sign in which the planet is located.")
    point_type: PointType = Field(description="The type of the point.")
    house: Optional[Houses] = Field(description="The house in which the planet is located.")
    retrograde: Optional[bool] = Field(default=None, description="The retrograde status of the planet.")


class BirthDataModel(BaseModel):
    """
    The model for the birth data.
    """

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
    zodiac_type: ZodiacType = Field(description="The type of zodiac used.")
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

    # Axial Cusps
    asc: PlanetModel = Field(description="The data of the ascendant.")
    dsc: PlanetModel = Field(description="The data of the descendant.")
    mc: PlanetModel = Field(description="The data of the midheaven.")
    ic: PlanetModel = Field(description="The data of the imum coeli.")
    
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
    lunar_phase: Optional[LunarPhaseModel] = Field(description="The lunar phase of the subject.")


class BirthDataResponseModel(BaseModel):
    """
    The response model for the Birth Data endpoint.
    """
    status: str = Field(description="The status of the response.")
    data: BirthDataModel = Field(description="The data of the subject.")


class BirthChartResponseModel(BaseModel):
    """
    The response model for the Birth Chart endpoint.
    """
    status: str = Field(description="The status of the response.")
    data: BirthDataModel = Field(description="The data of the subject.")
    chart: str = Field(description="The SVG chart of the birth chart.")
    aspects: list[AspectModel] = Field(description="The aspects of the birth chart.")


class DoubleDataModel(BaseModel):
    """
    The model for the data of two subjects.
    """
    first_subject: AstrologicalSubjectModel = Field(description="The data of the first subject.")
    second_subject: AstrologicalSubjectModel = Field(description="The data of the second subject.")


class TransitDataModel(BaseModel):
    """
    The model for the data of two subjects.
    """
    first_subject: AstrologicalSubjectModel = Field(description="The data of the first subject.")
    transit: AstrologicalSubjectModel = Field(description="The data of the second subject.")


class CompositeDataModel(BaseModel):
    """
    The model for the data of the composite chart.
    """
    composite_subject: CompositeSubjectModel = Field(description="The data of the composite chart.")
    first_subject: AstrologicalSubjectModel = Field(description="The data of the first subject.")
    second_subject: AstrologicalSubjectModel = Field(description="The data of the second subject.")


class SynastryChartResponseModel(BaseModel):
    """
    The response model for the Synastry.
    """
    status: str = Field(description="The status of the response.")
    data: DoubleDataModel = Field(description="The data of the two subjects.")
    chart: str = Field(description="The SVG chart of the synastry.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects.")


class TransitChartResponseModel(BaseModel):
    """
    The response model for the Transit.
    """
    status: str = Field(description="The status of the response.")
    data: TransitDataModel = Field(description="The data of the two subjects.")
    chart: str = Field(description="The SVG chart of the transit.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects.")


class TransitAspectsResponseModel(BaseModel):
    """
    The response model for the Transit Data endpoint.
    """
    status: str = Field(description="The status of the response.")
    data: TransitDataModel = Field(description="The data of the two subjects.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects.")


class RelationshipScoreResponseModel(BaseModel):
    """
    The response model for the Relationship Score endpoint.
    """

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


class CompositeChartResponseModel(BaseModel):
    """
    The response model for the Composite Chart endpoint.
    """

    status: str = Field(description="The status of the response.")
    data: CompositeDataModel = Field(description="The data of the subjects and the composite chart.")
    chart: str = Field(description="The SVG chart of the composite chart.")
    aspects: list[AspectModel] = Field(description="The aspects between the two subjects.")


class CompositeAspectsResponseModel(BaseModel):
    """
    The response model for the Composite Aspects endpoint.
    """

    status: str = Field(description="The status of the response.")
    data: CompositeDataModel = Field(description="The data of the subjects and the composite chart.")
    aspects: list[AspectModel] = Field(description="A list with the aspects between the two subjects.")