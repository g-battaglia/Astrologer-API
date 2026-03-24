---
title: 'Moon Phase'
description: 'Get detailed lunar phase data for any date, time, and location. Includes illumination, upcoming phases, eclipses, sunrise/sunset, and zodiac signs.'
order: 10
---

# Moon Phase Endpoint

## `POST /api/v5/moon-phase`

> **[View Complete Example](../examples/moon_phase)**

This endpoint returns detailed moon phase information for a specific date/time and geographic location. It computes lunar illumination, phase timing, upcoming major phases, eclipse predictions, and solar data (sunrise/sunset, sun position).

Unlike other endpoints, this uses a **simplified flat request model** — no `subject` wrapper, no `name`, `city`, or `nation` fields. Only date/time and geographic coordinates are required.

**Important:** This endpoint uses strict validation. Unknown/extra fields (e.g., `name`, `city`, `nation`) in the request body will be rejected with a `422` error.

### Use Cases

-   Displaying current moon phase in an app.
-   Tracking lunar cycles for gardening, fishing, or wellness apps.
-   Showing upcoming full/new moon dates.
-   Eclipse prediction features.
-   Sunrise/sunset calculators.

### Request Body

The request body contains date/time and location fields directly (no `subject` wrapper).

-   **`year`** (integer, required): Year of the event (1-3000).
-   **`month`** (integer, required): Month (1-12).
-   **`day`** (integer, required): Day (1-31).
-   **`hour`** (integer, required): Hour (0-23).
-   **`minute`** (integer, required): Minute (0-59).
-   **`second`** (integer, optional): Seconds (0-59, default: 0).
-   **`latitude`** (float, required): Latitude (-90 to 90).
-   **`longitude`** (float, required): Longitude (-180 to 180).
-   **`timezone`** (string, required): IANA timezone identifier (e.g., `"Europe/London"`, `"America/New_York"`).
-   **`using_default_location`** (boolean, optional): Metadata flag indicating default location (default: false).
-   **`location_precision`** (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: 0). This is display rounding only — calculations always use the full-precision input coordinates.

#### Complete Request Example

```json
{
    "year": 1993,
    "month": 10,
    "day": 10,
    "hour": 12,
    "minute": 12,
    "second": 0,
    "latitude": 51.5074,
    "longitude": -0.1276,
    "timezone": "Europe/London",
    "using_default_location": false,
    "location_precision": 4
}
```

#### Minimal Request Example

```json
{
    "year": 1993,
    "month": 10,
    "day": 10,
    "hour": 12,
    "minute": 12,
    "latitude": 51.5074,
    "longitude": -0.1276,
    "timezone": "Europe/London"
}
```

### Response Body

The response contains `status` and a `moon_phase_overview` object with the following sections:

#### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"OK"` on success. |
| `moon_phase_overview.timestamp` | integer | Unix timestamp of the requested moment. |
| `moon_phase_overview.datestamp` | string | Human-readable date/time string (RFC 2822 format). |

#### Moon Section (`moon_phase_overview.moon`)

| Field | Type | Description |
|-------|------|-------------|
| `phase` | float | Phase fraction (0.0 = New Moon, ~0.5 = Full Moon, 1.0 = next New Moon). |
| `phase_name` | string | One of: `"New Moon"`, `"Waxing Crescent"`, `"First Quarter"`, `"Waxing Gibbous"`, `"Full Moon"`, `"Waning Gibbous"`, `"Last Quarter"`, `"Waning Crescent"`. |
| `major_phase` | string | Nearest major phase (e.g., `"Last Quarter"`, `"Full Moon"`). |
| `stage` | string | `"waxing"` or `"waning"`. |
| `illumination` | string | Illuminated percentage as string (e.g., `"32%"`). |
| `age_days` | integer | Days since last New Moon. |
| `lunar_cycle` | string | Cycle completion percentage (e.g., `"80.736%"`). |
| `emoji` | string | Moon phase emoji (e.g., `"🌘"`). |
| `zodiac.sun_sign` | string | Sun sign abbreviation (e.g., `"Lib"`). |
| `zodiac.moon_sign` | string | Moon sign abbreviation (e.g., `"Leo"`). |
| `moonrise` | integer or null | Moonrise Unix timestamp. Null when data is unavailable. |
| `moonrise_timestamp` | string or null | Moonrise local time (HH:MM). Null when data is unavailable. |
| `moonset` | integer or null | Moonset Unix timestamp. Null when data is unavailable. |
| `moonset_timestamp` | string or null | Moonset local time (HH:MM). Null when data is unavailable. |
| `events` | object or null | Lunar events. Reserved for future use. |

#### Eclipse Section

| Field | Type | Description |
|-------|------|-------------|
| `moon.next_lunar_eclipse.timestamp` | integer | Unix timestamp of the next lunar eclipse. |
| `moon.next_lunar_eclipse.datestamp` | string | Date/time of the next lunar eclipse. |
| `moon.next_lunar_eclipse.type` | string | Eclipse type (e.g., `"Total Lunar Eclipse"`, `"Partial Lunar Eclipse"`). |
| `moon.next_lunar_eclipse.visibility_regions` | string or null | Visibility regions. Reserved for future use. |
| `sun.next_solar_eclipse.timestamp` | integer | Unix timestamp of the next solar eclipse. |
| `sun.next_solar_eclipse.datestamp` | string | Date/time of the next solar eclipse. |
| `sun.next_solar_eclipse.type` | string | Eclipse type (e.g., `"Annular Solar Eclipse"`, `"Partial Solar Eclipse"`). |
| `sun.next_solar_eclipse.visibility_regions` | string or null | Visibility regions. Reserved for future use. |

#### Detailed Moon Data (`moon.detailed`)

| Field | Type | Description |
|-------|------|-------------|
| `position` | object or null | Moon position data. Reserved for future use. |
| `visibility` | object or null | Moon visibility data. Reserved for future use. |
| `upcoming_phases` | object | Contains `new_moon`, `first_quarter`, `full_moon`, `last_quarter`. Each has `last` and `next` entries. |
| `upcoming_phases.*.last.timestamp` | integer | Unix timestamp of the last occurrence of this phase. |
| `upcoming_phases.*.last.datestamp` | string | Human-readable date of the last occurrence. |
| `upcoming_phases.*.last.days_ago` | integer or null | Days since the last occurrence. |
| `upcoming_phases.*.next.timestamp` | integer | Unix timestamp of the next occurrence. |
| `upcoming_phases.*.next.datestamp` | string | Human-readable date of the next occurrence. |
| `upcoming_phases.*.next.days_ahead` | integer or null | Days until the next occurrence. |
| `upcoming_phases.*.*.name` | string or null | Phase event name. Reserved for future use. |
| `upcoming_phases.*.*.description` | string or null | Phase event description. Reserved for future use. |
| `illumination_details.percentage` | float | Illumination as a number (e.g., `32.0`). |
| `illumination_details.visible_fraction` | float | Visible fraction from 0.0 to 1.0. |
| `illumination_details.phase_angle` | float | Phase angle in degrees. |

#### Sun Section (`moon_phase_overview.sun`)

| Field | Type | Description |
|-------|------|-------------|
| `sunrise` | integer | Sunrise as Unix timestamp. |
| `sunrise_timestamp` | string | Sunrise as local time string (HH:MM format). |
| `sunset` | integer | Sunset as Unix timestamp. |
| `sunset_timestamp` | string | Sunset as local time string (HH:MM format). |
| `solar_noon` | string | Solar noon as local time string (HH:MM). |
| `day_length` | string | Day length as duration string (HH:MM). |
| `position.altitude` | float | Sun altitude in degrees above horizon. |
| `position.azimuth` | float | Sun azimuth in degrees from north. |
| `position.distance` | float | Sun distance in kilometers. |

> **Note on naming:** `sunrise` and `sunset` are Unix timestamps (integers). `sunrise_timestamp` and `sunset_timestamp` are human-readable local time strings — the `_timestamp` suffix refers to the formatted representation, not a Unix timestamp.

#### Location Section (`moon_phase_overview.location`)

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | string | Latitude rounded to `location_precision` decimal places (e.g., `"52"` with precision 0, `"51.5074"` with precision 4). |
| `longitude` | string | Longitude rounded to `location_precision` decimal places (e.g., `"0"` with precision 0, `"-0.1276"` with precision 4). |
| `precision` | integer | The `location_precision` value that was used for rounding. |
| `using_default_location` | boolean | Whether default location metadata was set. |
| `note` | string or null | Location note. Reserved for future use. |

### Error Responses

This endpoint returns `422 Unprocessable Entity` in the following cases:

-   **Missing required fields**: Any of `year`, `month`, `day`, `hour`, `minute`, `latitude`, `longitude`, or `timezone` is omitted.
-   **Invalid timezone**: The `timezone` value is not a valid IANA timezone identifier (e.g., `"Foo/Bar"`).
-   **Out-of-range values**: Coordinates outside valid ranges (latitude: -90 to 90, longitude: -180 to 180), or time fields outside their ranges.
-   **Extra/unknown fields**: Any field not listed above (e.g., `name`, `city`, `nation`, `subject`) is sent. This endpoint uses strict validation and rejects unknown fields.
