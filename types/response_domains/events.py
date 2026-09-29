"""Events response models."""

from typing import Optional

from pydantic import Field

from kerykeion import (
    HeliacalEventModel,
    IngressModel,
    LunarEclipseModel,
    LunationModel,
    MundaneAspectModel,
    OccultationModel,
    SolarEclipseModel,
    StationModel,
)
from kerykeion.schemas import (
    PlanetaryPhenomenaModel,
)


from ..response_core import StatusResponseModel, SolarPhaseThresholdsModel


class EclipseSearchResponseModel(StatusResponseModel):
    """Response payload for eclipse search results."""

    solar_eclipses: list[SolarEclipseModel] = Field(
        default_factory=list,
        description="List of solar eclipses found.",
    )
    lunar_eclipses: list[LunarEclipseModel] = Field(
        default_factory=list,
        description="List of lunar eclipses found.",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Search latitude (None for global search).",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Search longitude (None for global search).",
    )


class LunationsResponseModel(StatusResponseModel):
    """Response payload for a lunation search over a date range."""

    start_jd: Optional[float] = Field(default=None, description="Resolved start of the scan window, as a Julian Day.")
    end_jd: Optional[float] = Field(default=None, description="Resolved end of the scan window, as a Julian Day.")
    lunations: list[LunationModel] = Field(
        default_factory=list,
        description="Ordered lunations (new, first_quarter, full, last_quarter) with Sun/Moon positions.",
    )


class RetrogradeStationsResponseModel(StatusResponseModel):
    """Response payload for a retrograde/direct station search over a date range."""

    stations: list[StationModel] = Field(
        default_factory=list,
        description="Ordered planetary stations (SR=retrograde, SD=direct) with zodiac positions.",
    )


class SignIngressesResponseModel(StatusResponseModel):
    """Response payload for a zodiac sign ingress search over a date range."""

    ingresses: list[IngressModel] = Field(
        default_factory=list,
        description="Ordered sign ingresses (30 degree boundary crossings) with from/to signs and retrograde flag.",
    )


class MundaneAspectsResponseModel(StatusResponseModel):
    """Response payload for a mundane aspectarian search over a date range."""

    aspects: list[MundaneAspectModel] = Field(
        default_factory=list,
        description=("Ordered exact transiting-to-transiting aspects, each with its UTC instant, both bodies' longitudes/signs and retrograde flags."),
    )


class PlanetaryPhenomenaResponseModel(StatusResponseModel):
    """Response payload for planetary phenomena calculation."""

    iso_datetime: Optional[str] = Field(default=None, description="ISO datetime of the calculation moment.")
    julian_day: Optional[float] = Field(default=None, description="Julian Day of the calculation moment.")
    phenomena: list[PlanetaryPhenomenaModel] = Field(
        default_factory=list,
        description="List of planetary phenomena (phase_angle, elongation, magnitude, solar_phase, etc.).",
    )
    solar_phase_thresholds: Optional[SolarPhaseThresholdsModel] = Field(
        default=None,
        description="Band half-widths, in degrees, that classified each entry's `solar_phase` — the request's override when one was sent, the traditional defaults otherwise.",
    )


class HeliacalEventsResponseModel(StatusResponseModel):
    """Response payload for heliacal events search."""

    events: list[HeliacalEventModel] = Field(
        default_factory=list,
        description="List of heliacal events (rising, setting, evening first, morning last).",
    )


class OccultationSearchResponseModel(StatusResponseModel):
    """Response payload for stellar occultation search."""

    events: list[OccultationModel] = Field(
        default_factory=list,
        description="List of occultation events.",
    )
