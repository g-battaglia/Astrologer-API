"""
Validation helpers for input validation and error message enrichment.

This module provides utilities to generate helpful error messages when users
send incorrect field names in their requests.
"""

from __future__ import annotations

from typing import Any

# Mapping of common incorrect field names to their correct alternatives
FIELD_CORRECTIONS: dict[str, str] = {
    "country": "nation",
    "state": "city (include state in city field, e.g. 'Amherst, Massachusetts')",
    "house_system": "houses_system_identifier",
    "lat": "latitude",
    "lng": "longitude",
    "lon": "longitude",
    "tz": "timezone",
    "name_first": "name",
    "first_name": "name",
    "last_name": "name",
    "birth_year": "year",
    "birth_month": "month",
    "birth_day": "day",
    "birth_hour": "hour",
    "birth_minute": "minute",
    "dob": "year, month, day (use separate fields)",
    "date_of_birth": "year, month, day (use separate fields)",
    "time_of_birth": "hour, minute (use separate fields)",
    "location": "latitude, longitude, timezone (use separate fields)",
    "coordinates": "latitude, longitude (use separate fields)",
    "zodiac": "zodiac_type",
    "sidereal": "sidereal_mode",
    "ayanamsha": "sidereal_mode",
    "perspective": "perspective_type",
    "house_sys": "houses_system_identifier",
    "houses": "houses_system_identifier",
    # v4 → v5/v6 field renames (two-subject endpoints)
    "subject": "first_subject (on transit, synastry, and composite endpoints)",
    "transit": "transit_subject",
}

# Rendering-only parameters — only available on /chart/ endpoints, not /chart-data/
RENDERING_ONLY_FIELDS: set[str] = {
    "theme",
    "language",
    "split_chart",
    "transparent_background",
    "show_house_position_comparison",
    "show_cusp_position_comparison",
    "show_degree_indicators",
    "show_aspect_icons",
    "custom_title",
    "style",
    "glyph_size",
    "show_zodiac_background_ring",
    "show_diurnality",
    "show_motion_state",
    "show_out_of_bounds",
    "show_aspect_movement",
    "show_relationship_score",
    "show_ayanamsa_value",
    "show_polar_fallback_note",
}

# Fields valid on SubjectModel but NOT on TransitSubjectModel
TRANSIT_SUBJECT_FIELD_HINTS: dict[str, str] = {
    "zodiac_type": "Set 'zodiac_type' on first_subject or at request level, not on transit_subject.",
    "sidereal_mode": "Set 'sidereal_mode' on first_subject or at request level, not on transit_subject.",
    "perspective_type": "Set 'perspective_type' on first_subject or at request level, not on transit_subject.",
    "houses_system_identifier": ("Set 'houses_system_identifier' on first_subject or at request level, not on transit_subject."),
}


def get_field_correction(field_name: str) -> str | None:
    """
    Get the correction suggestion for an incorrect field name.

    Args:
        field_name: The incorrect field name from the request.

    Returns:
        A correction message if a known correction exists, None otherwise.
    """
    normalized = field_name.lower().strip()
    return FIELD_CORRECTIONS.get(normalized)


def format_extra_field_error(field_name: str, location: list[Any]) -> str:
    """
    Format an error message for an extra field, including correction if available.

    Uses context from the location path to provide targeted guidance:
    - transit_subject fields → guide to first_subject
    - rendering params on data endpoints → guide to /chart/ endpoints
    - common typos → suggest the correct field name

    Args:
        field_name: The extra field name that was sent.
        location: The path location of the field in the request body.

    Returns:
        A formatted error message with contextual correction.
    """
    normalized = field_name.lower().strip()
    location_str = ".".join(str(loc) for loc in location if loc != "body")

    # Context: transit_subject — guide to first_subject for config fields
    if any(str(loc) == "transit_subject" for loc in location):
        hint = TRANSIT_SUBJECT_FIELD_HINTS.get(normalized)
        if hint:
            return f"Extra field '{field_name}' is not allowed in '{location_str}'. {hint}"

    # Context: rendering-only params sent to a route that does not take them.
    # No per-field claim about what the route renders: an earlier wording said
    # "this endpoint renders nothing it applies to", which is true of the
    # info-panel flags on the two progression chart routes and false of the
    # wheel flags there (show_degree_indicators applies to a wheel those routes
    # do return — they reject it because their models carry only their own
    # documented parameters, not the full rendering set).
    if normalized in RENDERING_ONLY_FIELDS:
        return (
            f"'{field_name}' is a rendering parameter and is not accepted here: "
            f"/chart-data/ and /context/ endpoints return no SVG, and /chart/secondary-progressions and "
            f"/chart/solar-arc-directions return only a wheel and a grid and accept only their documented "
            f"parameters. Remove '{field_name}', or use a /chart/ endpoint that returns a full chart."
        )

    # General field corrections (typos, v4→v5/v6 renames)
    correction = FIELD_CORRECTIONS.get(normalized)
    if correction:
        return f"Extra field '{field_name}' is not allowed in '{location_str}'. Did you mean '{correction}'?"

    return f"Extra field '{field_name}' is not allowed in '{location_str}'."
