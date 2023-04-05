"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""


from pydantic import BaseModel, Field


# Create a response model from the above data
class AstrologicalObjectModel(BaseModel):
    name: str = "Sun"
    quality: str = "Cardinal"
    element: str = "Fire"
    sign: str = "Ari"
    sign_num: int = 0
    position: float = 5.435
    abs_pos: float = 5.435
    emoji: str = "♈️"
    point_type: str = "Planet"
    house: str = "First House"
    retrograde: bool = False


class AstrologicalHouseModel(BaseModel):
    name: str = "First House"
    quality: str = "Cardinal"
    element: str = "Air"
    sign: str = "Lib"
    sign_num: int = 6
    position: float = 23.601816240113607
    abs_pos: float = 203.6018162401136
    emoji: str = "♎️"
    point_type: str = "House"


class LunarPhaseModel(BaseModel):
    degrees_between_s_m: int = 215
    moon_phase: int = 17
    sun_phase: int = 16
    moon_emoji: str = "🌖"


class AstrologicalDataModel(BaseModel):
    """Astrological data model."""

    name: str = Field("Mario Rossi", description="Name of the subject")
    year: int = Field(1980, description="Year of birth")
    month: int = Field(1, description="Month of birth")
    day: int = Field(1, description="Day of birth")
    hour: int = Field(0, description="Hour of birth")
    minute: int = Field(0, description="Minute of birth")
    city: str = Field("Rome", description="City of birth")
    nation: str = Field("Italy", description="Nation of birth")
    lng: float = Field(12.496366, description="Longitude of birth")
    lat: float = Field(41.902783, description="Latitude of birth")
    tz_str: str = Field("CET", description="Timezone of birth")
    zodiac_type: str = Field("Tropic", description="Zodiac type")
    local_time: float = Field(0.0, description="Local time")
    utc_time: float = Field(0.0, description="UTC time")
    julian_day: float = Field(0.0, description="Julian day")

    # Planets
    sun: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Sun")
    moon: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Moon")
    mercury: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Mercury")
    venus: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Venus")
    mars: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Mars")
    jupiter: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Jupiter")
    saturn: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Saturn")
    uranus: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Uranus")
    neptune: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Neptune")
    pluto: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Pluto")

    # Houses
    first_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="First House")
    second_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Second House")
    third_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Third House")
    fourth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Fourth House")
    fifth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Fifth House")
    sixth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Sixth House")
    seventh_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Seventh House")
    eighth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Eighth House")
    ninth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Ninth House")
    tenth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Tenth House")
    eleventh_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Eleventh House")
    twelfth_house: AstrologicalHouseModel = Field(AstrologicalHouseModel(), description="Twelfth House")

    # Nodes
    mean_node: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="Mean Node")
    true_node: AstrologicalObjectModel = Field(AstrologicalObjectModel(), description="True Node")

    # Lunar phase
    lunar_phase: LunarPhaseModel = Field(LunarPhaseModel(), description="Lunar phase")


class AstrologicalDataResponseModel(BaseModel):
    """Astrological data response model."""

    data: AstrologicalDataModel = Field(AstrologicalDataModel(), description="Astrological data")
    status: str = Field("OK", description="Status of the response")


class AstrologicalBirthChartResponseModel(BaseModel):
    """Astrological chart response model."""

    chart: str = Field("SVG_Object", description="Astrological chart SVG in string format")
    data: str = Field(AstrologicalDataModel(), description="Astrological data")
    status: str = Field("OK", description="Status of the response")
