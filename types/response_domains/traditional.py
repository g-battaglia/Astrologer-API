"""Traditional response models."""

from pydantic import Field

from kerykeion.schemas import (
    ZodiacalReleasingModel,
    ProfectionsModel,
    FirdariaModel,
    HoraryIndicatorsModel,
)


from ..response_core import StatusResponseModel


class ZodiacalReleasingResponseModel(StatusResponseModel):
    """Response payload for zodiacal releasing calculation."""

    zodiacal_releasing: ZodiacalReleasingModel = Field(
        description=("Zodiacal-releasing result: the lot, its sign and degree, the nested L1 periods (with sub-periods), and the current period chain for the target date."),
    )


class ProfectionsResponseModel(StatusResponseModel):
    """Response payload for annual profections."""

    profections: ProfectionsModel = Field(
        description=("Annual profections: the current year (age, profected house, sign, Lord of the Year, anniversary boundaries) and the surrounding window of years."),
    )


class FirdariaResponseModel(StatusResponseModel):
    """Response payload for firdaria time-lord periods."""

    firdaria: FirdariaModel = Field(
        description=("Firdaria timeline: sect, the major periods with their sub-lord periods, and the current period/sub-period for the target date."),
    )


class HoraryIndicatorsResponseModel(StatusResponseModel):
    """Response payload for horary indicators."""

    horary_indicators: HoraryIndicatorsModel = Field(
        description=("Horary indicators: querent and quesited significators, the Ascendant degree, the considerations before judgment (as stable keys), and the chart's mutual receptions."),
    )
