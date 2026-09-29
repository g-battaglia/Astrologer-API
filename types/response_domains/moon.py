"""Moon response models."""

from typing import Optional

from pydantic import BaseModel, Field


from ..response_core import StatusResponseModel


class MoonVocWindowEntryModel(BaseModel):
    """One void-of-course window in a range scan (API JSON shape)."""

    moon_sign: str = Field(description="Sign the Moon is leaving (three-letter code).")
    next_sign: str = Field(description="Sign the Moon ingresses into, ending the void.")
    void_start: str = Field(description="Start of the void window, ISO-8601 UTC.")
    void_start_local: Optional[str] = Field(default=None, description="Void start in the request timezone (when provided).")
    void_end: str = Field(description="End of the void window (= ingress), ISO-8601 UTC.")
    void_end_local: Optional[str] = Field(default=None, description="Void end in the request timezone (when provided).")
    duration_minutes: float = Field(description="Window length in minutes.")
    # Forward reference: MoonAspectEventModel is defined later in this module
    # (next to the single-moment MoonVocModel); pydantic resolves it lazily.
    last_aspect: Optional["MoonAspectEventModel"] = Field(
        default=None,
        description="The aspect that opened the void (none for a whole-sign void).",
    )


class MoonVocWindowsResponseModel(StatusResponseModel):
    """Response payload for void-of-course Moon windows over a date range."""

    windows: list[MoonVocWindowEntryModel] = Field(
        default_factory=list,
        description="Chronologically ordered, non-overlapping void windows intersecting the range (unclipped).",
    )


class MoonAspectEventModel(BaseModel):
    """A single exact aspect the Moon perfects to another body."""

    planet: str = Field(description="The body the Moon aspects (Sun, Mercury, …).")
    aspect: str = Field(description="Aspect name (conjunction, sextile, square, trine, opposition).")
    degrees: float = Field(description="Aspect angle in degrees (0, 60, 90, 120, 180).")
    time: str = Field(description="Exact aspect time, ISO-8601 UTC.")
    time_local: Optional[str] = Field(
        default=None,
        description="Exact aspect time, ISO-8601 in the request timezone (null when the request carries no timezone).",
    )


class MoonVocModel(BaseModel):
    """Void-of-course state for a moment: the Moon makes no further exact aspect
    before leaving its current sign during the void window."""

    is_void: bool = Field(description="True if the Moon is void of course at the requested moment.")
    moon_sign: str = Field(description="Sign the Moon currently occupies.")
    next_sign: str = Field(description="Sign the Moon ingresses into next.")
    ingress: str = Field(description="Time the Moon enters the next sign, ISO-8601 UTC.")
    ingress_local: str = Field(description="Ingress, ISO-8601 in the request timezone.")
    void_start: str = Field(description="Start of the void window (Moon's last in-sign aspect), ISO-8601 UTC.")
    void_start_local: str = Field(description="Void-window start, ISO-8601 in the request timezone.")
    void_end: str = Field(description="End of the void window (= ingress), ISO-8601 UTC.")
    void_end_local: str = Field(description="Void-window end, ISO-8601 in the request timezone.")
    last_aspect: Optional[MoonAspectEventModel] = Field(default=None, description="The Moon's last exact aspect before ingress (none if the whole sign is void).")
    next_aspect: Optional[MoonAspectEventModel] = Field(
        default=None,
        description="The Moon's first exact aspect after the ingress, in the next sign — the aspect that ends the void lull (none only if the Moon makes no aspect throughout the next sign).",
    )


class MoonVocResponseModel(StatusResponseModel):
    """Response payload for the void-of-course Moon endpoint."""

    moon_voc: MoonVocModel
