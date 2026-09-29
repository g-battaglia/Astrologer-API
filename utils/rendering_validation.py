"""Validation at the API boundary for user-controlled SVG rendering values."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

from kerykeion.settings import DEFAULT_CHART_COLORS


MAX_COLOR_OVERRIDES = len(DEFAULT_CHART_COLORS)
MAX_COLOR_VALUE_LENGTH = 96
MAX_LANGUAGE_ENTRIES = 256
MAX_LANGUAGE_KEY_LENGTH = 64
MAX_LANGUAGE_VALUE_LENGTH = 256

_COLOR_KEYS = frozenset(DEFAULT_CHART_COLORS)
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{1}|[0-9a-fA-F]{3}|[0-9a-fA-F]{5})?\Z")
_NAMED_COLOR = re.compile(r"[a-zA-Z]{1,32}\Z")
_CSS_FUNCTION_COLOR = re.compile(
    r"(?:rgb|rgba|hsl|hsla)\(\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)%?"
    r"(?:\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)%?){2,3}\s*\)\Z",
    re.IGNORECASE,
)
_CSS_VARIABLE = re.compile(r"var\(--[a-zA-Z][a-zA-Z0-9_-]{0,63}\)\Z")
_LANGUAGE_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")


def _is_safe_color(value: str) -> bool:
    return bool(
        _HEX_COLOR.fullmatch(value)
        or _NAMED_COLOR.fullmatch(value)
        or _CSS_FUNCTION_COLOR.fullmatch(value)
        or _CSS_VARIABLE.fullmatch(value)
    )


def validate_colors_settings(value: Mapping[str, str] | None) -> dict[str, str] | None:
    """Return a validated copy of chart-color overrides.

    ChartDrawer interpolates these values into both XML attributes and CSS.
    Positive validation is therefore required: XML well-formedness alone does
    not prevent an injected ``onload``/``onmouseover`` attribute.
    """
    if value is None:
        return None
    if len(value) > MAX_COLOR_OVERRIDES:
        raise ValueError(f"colors_settings accepts at most {MAX_COLOR_OVERRIDES} entries.")

    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in _COLOR_KEYS:
            raise ValueError(f"Unknown colors_settings key: {key!r}.")
        if not isinstance(raw, str):
            raise ValueError(f"colors_settings[{key!r}] must be a CSS color string.")
        color = raw.strip()
        if not color or len(color) > MAX_COLOR_VALUE_LENGTH or not _is_safe_color(color):
            raise ValueError(
                f"colors_settings[{key!r}] must be a plain CSS color: hex, named, "
                "rgb()/rgba()/hsl()/hsla(), or var(--name) without a fallback."
            )
        out[key] = color
    return out


def validate_language_pack(value: Mapping[str, str] | None) -> dict[str, str] | None:
    """Bound custom labels and reject control characters before SVG rendering."""
    if value is None:
        return None
    if len(value) > MAX_LANGUAGE_ENTRIES:
        raise ValueError(f"language_pack accepts at most {MAX_LANGUAGE_ENTRIES} entries.")

    out: dict[str, str] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not _LANGUAGE_KEY.fullmatch(key):
            raise ValueError(f"Invalid language_pack key: {key!r}.")
        if not isinstance(raw, str):
            raise ValueError(f"language_pack[{key!r}] must be a string.")
        if len(raw) > MAX_LANGUAGE_VALUE_LENGTH:
            raise ValueError(f"language_pack[{key!r}] exceeds {MAX_LANGUAGE_VALUE_LENGTH} characters.")
        if any(ord(char) < 32 and char not in "\t\n\r" for char in raw):
            raise ValueError(f"language_pack[{key!r}] contains a control character.")
        out[key] = raw
    return out


def ensure_finite(value: float | int | None, *, field: str) -> float | int | None:
    """Reject NaN and infinities before they reach astronomical calculations."""
    if value is not None and isinstance(value, (float, int)) and not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number.")
    return value
