"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from pydantic import BaseModel, Field
from datetime import datetime

now = datetime.now()

class SubjectModel(BaseModel):
    """Astrological type for a subject."""

    name: str = Field(description="The name of the person to get the Birth Chart for.", example="Mario Rossi", type="string")
    year: int = Field(description="The year of birth.", example=1946, type="integer")
    month: int = Field(description="The month of birth.", example=6, type="integer")
    day: int = Field(description="The day of birth.", example=16, type="integer")
    hour: int = Field(description="The hour of birth.", example=10, type="integer")
    minute: int = Field(description="The minute of birth.", example=10, type="integer")
    longitude: float = Field(default=0, description="The longitude of the birth location. Defaults on London.", example=12.4963655, type="number")
    latitude: float = Field(default=51.4825766, description="The latitude of the birth location. Defaults on London.", example=41.9027835, type="number")
    city: str = Field(default="London", description="The name of city of birth.", example="Roma", type="string")
    timezone: str = Field(default="Europe/London", description="The timezone of the birth location.", example="Europe/Rome", type="string")
    language: str = Field(default="EN", description="The language of the birth chart, currently just English, Italian and Portuguese are available.", example="IT", type="string")


class TransitModel(BaseModel):
    """
    Astrological type for a transit.
    """

    year: int = Field(default=now.year, description="The year of the transit.", type="integer")
    month: int = Field(default=now.month, description="The month of the transit.", type="integer")
    day: int = Field(default=now.day, description="The day of the transit.", type="integer")
    hour: int = Field(default=now.hour, description="The hour of the transit.", type="integer")
    minute: int = Field(default=now.minute, description="The minute of the transit.", type="integer")


class GeoCity(BaseModel):
    """
    Geo type for a city.
    """

    city: str = Field(description="The name of the city.", example="Roma", type="string")
    country: str = Field(description="2 letters initial of the country", example="IT", type="string")
