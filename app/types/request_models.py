from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, get_args, Union
from kerykeion.kr_types.kr_models import ActiveAspect
from pytz import all_timezones
from kerykeion.kr_types.kr_literals import KerykeionChartTheme, KerykeionChartLanguage, SiderealMode, ZodiacType, HousesSystemIdentifier, PerspectiveType, AxialCusps, Planet
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from abc import ABC

class AbstractBaseSubjectModel(BaseModel, ABC):
    year: int = Field(description="The year of birth.", examples=[1980])
    month: int = Field(description="The month of birth.", examples=[12])
    day: int = Field(description="The day of birth.", examples=[12])
    hour: int = Field(description="The hour of birth.", examples=[12])
    minute: int = Field(description="The minute of birth.", examples=[12])
    longitude: Optional[float] = Field(description="The longitude of the birth location. Defaults on London.", examples=[0], default=None)
    latitude: Optional[float] = Field(description="The latitude of the birth location. Defaults on London.", examples=[51.4825766], default=None)
    city: str = Field(description="The name of city of birth.", examples=["London"])
    nation: Optional[str] = Field(default="null", description="The name of the nation of birth.", examples=["GB"])
    timezone: Optional[str] = Field(description="The timezone of the birth location.", examples=["Europe/London"], default=None)
    geonames_username: Optional[str] = Field(description="The username for the Geonames API.", examples=[None], default=None)


    @field_validator("longitude")
    def validate_longitude(cls, value):
        if value is None:
            return None
        if value < -180 or value > 180:
            raise ValueError(f"Invalid longitude '{value}'. Please use a value between -180 and 180.")
        return value

    @field_validator("latitude")
    def validate_latitude(cls, value):
        if value is None:
            return None
        if value < -90 or value > 90:
            raise ValueError(f"Invalid latitude '{value}'. Please use a value between -90 and 90.")
        return value

    @field_validator("timezone")
    def validate_timezone(cls, value):
        if value is None:
            return None
        if value not in all_timezones:
            raise ValueError(f"Invalid timezone '{value}'. Please use a valid timezone. You can find a list of valid timezones at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.")
        return value

    @field_validator("month")
    def validate_month(cls, value):
        if value is None:
            return None
        if value < 1 or value > 12:
            raise ValueError(f"Invalid month '{value}'. Please use a value between 1 and 12.")
        return value

    @field_validator("day")
    def validate_day(cls, value, values):
        month = values.data.get("month")

        if month in [1, 3, 5, 7, 8, 10, 12]:
            if value < 1 or value > 31:
                raise ValueError(f"Invalid day '{value}'. Please use a value between 1 and 31.")
        elif month in [4, 6, 9, 11]:
            if value < 1 or value > 30:
                raise ValueError(f"Invalid day '{value}'. Please use a value between 1 and 30.")
        elif month == 2:
            if value < 1 or value > 29:
                raise ValueError(f"Invalid day '{value}'. Please use a value between 1 and 29.")
        return value

    @field_validator("hour")
    def validate_hour(cls, value):
        if value is None:
            return None
        if value < 0 or value > 23:
            raise ValueError(f"Invalid hour '{value}'. Please use a value between 0 and 23.")
        return value

    @field_validator("minute")
    def validate_minute(cls, value):
        if value is None:
            return None
        if value < 0 or value > 59:
            raise ValueError(f"Invalid minute '{value}'. Please use a value between 0 and 59.")
        return value

    @field_validator("year")
    def validate_year(cls, value):
        if value is None:
            return None
        if value < 1800 or value > 2100:
            raise ValueError(f"Invalid year '{value}'. Please use a value between 1800 and 2300.")
        return value

    @field_validator("nation")
    def validate_nation(cls, value):
        if not value:
            return "null"

        if len(value) != 2 or not value.isalpha():  # Esattamente 2 lettere
            raise ValueError(
                f"Invalid nation code: '{value}'. It must be a 2-letter country code following the ISO 3166-1 alpha-2 standard."
            )

        return value

    @model_validator(mode="after")
    def check_lat_lng_tz_or_geonames(self):
        lat = self.latitude
        lng = self.longitude
        tz = self.timezone
        geonames = self.geonames_username

        # If latitude, longitude, and timezone are all missing, geonames_username must be provided
        if lat is None and lng is None and tz is None:
            if not geonames:
                raise ValueError("Either provide latitude, longitude, timezone or specify geonames_username.")

        # If any one of latitude, longitude, or timezone is missing (but not all), either fill them all or use geonames_username
        missing_fields = sum(1 for f in [lat, lng, tz] if f is None)
        if 0 < missing_fields < 3 and not geonames:
            raise ValueError("Please provide all missing fields (latitude, longitude, timezone) or specify geonames_username.")

        if geonames and (lat or lng or tz):
            self.latitude = None
            self.longitude = None
            self.timezone = None

        return self

class SubjectModel(AbstractBaseSubjectModel):
    """
    The request model for the Birth Chart endpoint.
    """

    name: str = Field(description="The name of the person to get the Birth Chart for.", examples=["John Doe"])
    zodiac_type: Optional[ZodiacType] = Field(default="Tropic", description="The type of zodiac used (Tropic or Sidereal).", examples=list(get_args(ZodiacType)))
    sidereal_mode: Union[SiderealMode, None] = Field(default=None, description="The sidereal mode used.", examples=[None])
    perspective_type: Union[PerspectiveType, None] = Field(default="Apparent Geocentric", description="The perspective type used.", examples=list(get_args(PerspectiveType)))
    houses_system_identifier: Union[HousesSystemIdentifier, None] = Field(
        default="P",
        examples=['P'],
        description=(
            "The house system to use. The following are the available house systems: "
            "A = equal "
            "B = Alcabitius "
            "C = Campanus "
            "D = equal (MC) "
            "F = Carter poli-equ. "
            "H = horizon/azimut "
            "I = Sunshine "
            "i = Sunshine/alt. "
            "K = Koch "
            "L = Pullen SD "
            "M = Morinus "
            "N = equal/1=Aries "
            "O = Porphyry "
            "P = Placidus "
            "Q = Pullen SR "
            "R = Regiomontanus "
            "S = Sripati "
            "T = Polich/Page "
            "U = Krusinski-Pisa-Goelzer "
            "V = equal/Vehlow "
            "W = equal/whole sign "
            "X = axial rotation system/Meridian houses "
            "Y = APC houses "
            "Usually the standard is Placidus (P)"
        )
    )

    @field_validator("zodiac_type")
    def validate_zodiac_type(cls, value, info):
        if info.data.get('sidereal_mode') and value != "Sidereal":
            raise ValueError(f"Invalid zodiac_type '{value}'. Please use 'Sidereal' when sidereal_mode is set.")
        return value

    @field_validator("sidereal_mode")
    def validate_sidereal_mode(cls, value, info):
        # If sidereal mode is set, zodiac type must be Sidereal
        if value and info.data.get('zodiac_type') != "Sidereal":
            raise ValueError(f"Invalid sidereal_mode '{value}'. Please use 'Sidereal' as zodiac_type when sidereal_mode is set. If you want to use the default sidereal mode, do not set this field or set it to None.")
        return value

    @field_validator("perspective_type")
    def validate_perspective_type(cls, value, info):
        # If it's none, set it to the default value
        if not value:
            return "Apparent Geocentric"
        return value

    @field_validator("houses_system_identifier")
    def validate_houses_system_identifier(cls, value, info):
        # If it's none, set it to the default value
        if not value:
            return "P"
        return value

class TransitSubjectModel(AbstractBaseSubjectModel):
    ...

class BirthChartRequestModel(BaseModel):
    """
    The request model for the Birth Chart endpoint.
    """

    subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    theme: Optional[KerykeionChartTheme] = Field(default="classic", description="The theme of the chart.", examples=["classic", "light", "dark", "dark-high-contrast"])
    language: Optional[KerykeionChartLanguage] = Field(default="EN", description="The language of the chart.", examples=list(get_args(KerykeionChartLanguage)))
    wheel_only: Optional[bool] = Field(default=False, description="If set to True, only the zodiac wheel will be returned. No additional information will be displayed.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])

class SynastryChartRequestModel(BaseModel):
    """
    The request model for the Synastry Chart endpoint.
    """

    first_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    second_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    theme: Optional[KerykeionChartTheme] = Field(default="classic", description="The theme of the chart.", examples=["classic", "light", "dark", "dark-high-contrast"])
    language: Optional[KerykeionChartLanguage] = Field(default="EN", description="The language of the chart.", examples=list(get_args(KerykeionChartLanguage)))
    wheel_only: Optional[bool] = Field(default=False, description="If set to True, only the zodiac wheel will be returned. No additional information will be displayed.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])

class TransitChartRequestModel(BaseModel):
    """
    The request model for the Transit Chart endpoint.
    """

    first_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    transit_subject: TransitSubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    theme: Optional[KerykeionChartTheme] = Field(default="classic", description="The theme of the chart.", examples=["classic", "light", "dark", "dark-high-contrast"])
    language: Optional[KerykeionChartLanguage] = Field(default="EN", description="The language of the chart.", examples=list(get_args(KerykeionChartLanguage)))
    wheel_only: Optional[bool] = Field(default=False, description="If set to True, only the zodiac wheel will be returned. No additional information will be displayed.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])

class BirthDataRequestModel(BaseModel):
    """
    The request model for the Birth Data endpoint.
    """

    subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")


class RelationshipScoreRequestModel(BaseModel):
    """
    The request model for the Relationship Score endpoint.
    """

    first_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    second_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")


class SynastryAspectsRequestModel(BaseModel):
    """
    The request model for the Aspects endpoint.
    """

    first_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    second_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])

class NatalAspectsRequestModel(BaseModel):
    """
    The request model for the Birth Data endpoint.
    """

    subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])


class CompositeChartRequestModel(BaseModel):
    """
    The request model for the Synastry Chart endpoint.
    """

    first_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    second_subject: SubjectModel = Field(description="The name of the person to get the Birth Chart for.")
    theme: Optional[KerykeionChartTheme] = Field(default="classic", description="The theme of the chart.", examples=["classic", "light", "dark", "dark-high-contrast"])
    language: Optional[KerykeionChartLanguage] = Field(default="EN", description="The language of the chart.", examples=list(get_args(KerykeionChartLanguage)))
    wheel_only: Optional[bool] = Field(default=False, description="If set to True, only the zodiac wheel will be returned. No additional information will be displayed.")
    active_points: Optional[list[Union[Planet, AxialCusps]]] = Field(default=DEFAULT_ACTIVE_POINTS, description="The active points to display in the chart.", examples=[DEFAULT_ACTIVE_POINTS])
    active_aspects: Optional[list[ActiveAspect]] = Field(default=DEFAULT_ACTIVE_ASPECTS, description="The active aspects to display in the chart.", examples=[DEFAULT_ACTIVE_ASPECTS])
