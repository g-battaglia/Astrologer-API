# Astrologer API v5 Endpoints

This document describes the v5 REST API endpoints for the Astrologer API. All endpoints accept JSON payloads and return JSON responses.

## Base URL

```
https://astrologer.p.rapidapi.com
```

## Authentication

All requests require the following headers:

```
X-RapidAPI-Host: astrologer.p.rapidapi.com
X-RapidAPI-Key: YOUR_API_KEY
```

## Common Request Parameters

### Subject Model

Used across most endpoints to define a person's birth data:

```json
{
    "name": "John Doe",
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 12,
    "minute": 30,
    "second": 0,
    "city": "London",
    "nation": "GB",
    "timezone": "Europe/London",
    "longitude": -0.1278,
    "latitude": 51.5074,
    "altitude": null,
    "zodiac_type": "Tropical",
    "sidereal_mode": null,
    "custom_ayanamsa_t0": null,
    "custom_ayanamsa_ayan_t0": null,
    "perspective_type": "Apparent Geocentric",
    "houses_system_identifier": "P",
    "is_dst": null,
    "geonames_username": null
}
```

**Location Options:**

-   Provide `longitude`, `latitude`, and `timezone` for offline mode (recommended)
-   OR provide `geonames_username` to use GeoNames API for location lookup (requires city and nation)

### Chart Configuration Options

Available for `/charts/*` endpoints and `/api/v5/now/chart` (with SVG rendering):

-   `theme`: Visual theme ("classic", "dark", "light", "strawberry", "dark-high-contrast", "black-and-white")
-   `language`: Chart language ("EN", "IT", "FR", "ES", "PT", "CN", "RU", "TR", "DE", "HI")
-   `style`: Chart wheel layout — "classic" (default) or "modern" (concentric ring layout)
-   `show_zodiac_background_ring`: Boolean - show colored zodiac wedges behind the wheel, modern style only (default: true)
-   `double_chart_aspect_grid_type`: Aspect display for dual charts — "list" (default) or "table" (grid/matrix)
-   `split_chart`: Boolean - return separate `chart_wheel` and `chart_grid` SVG strings (default: false)
-   `transparent_background`: Boolean - render chart with transparent background instead of theme default
-   `show_house_position_comparison`: Boolean - include the house comparison table (set to false to hide it and widen the chart)
-   `show_cusp_position_comparison`: Boolean - include the cusp position comparison table for dual charts (default: true)
-   `show_degree_indicators`: Boolean - display radial lines and degree numbers for planet positions on the chart wheel (default: true)
-   `show_aspect_icons`: Boolean - display aspect icons on aspect lines (default: true)
-   `custom_title`: String ≤40 chars - temporary override for the rendered chart title (trimmed if blank)

### Computation Configuration Options

Available for **all** chart endpoints (both `/chart-data/*` and `/chart/*`):

-   `active_points`: Array of points to include (default: all major planets and points)
-   `active_aspects`: Array of aspect configurations with orbs
-   `distribution_method`: "weighted" (default) or "pure_count"
-   `custom_distribution_weights`: Custom weight mapping for element/quality distribution

**Note:** `/chart-data/*` endpoints return data only (no SVG) and do **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`). These parameters will be rejected with a 422 error if provided.

## Endpoints

### Health Check

**GET** `/health`

Returns API health status.

**Response:**

```json
{
    "status": "OK"
}
```

---

### Current Moment

#### Get Current Subject

**POST** `/api/v5/now/subject`

Returns astrological data for the current UTC time at Greenwich with optional configuration.

**Request:**

```json
{
    "name": "Now",
    "zodiac_type": "Tropical",
    "sidereal_mode": null,
    "perspective_type": "Apparent Geocentric",
    "houses_system_identifier": "P"
}
```

**Note:** All fields are optional. If not provided, defaults will be used (name="Now", zodiac_type="Tropical", perspective_type="Apparent Geocentric", houses_system_identifier="P").

**Response:**

```json
{
    "status": "OK",
    "subject": {
        /* AstrologicalSubjectModel */
    }
}
```

#### Get Current Chart

**POST** `/api/v5/now/chart`

Returns chart data and SVG for the current UTC time at Greenwich with optional subject and rendering configuration.

**Request:**

```json
{
  "name": "Now",
  "zodiac_type": "Tropical",
  "sidereal_mode": null,
  "perspective_type": "Apparent Geocentric",
  "houses_system_identifier": "P",
  "theme": "classic",
  "language": "EN",
  "style": "classic",
  "show_zodiac_background_ring": true,
  "double_chart_aspect_grid_type": "list",
  "split_chart": false,
  "transparent_background": false,
  "show_house_position_comparison": true,
  "show_cusp_position_comparison": true,
  "show_degree_indicators": true,
  "show_aspect_icons": true,
  "custom_title": null,
  "active_points": [...],
  "active_aspects": [...]
}
```

**Note:** All fields are optional. Subject configuration (name, zodiac_type, etc.) defaults to "Now" with Tropical zodiac. Rendering and computation options follow the standard chart configuration rules.

**Response:**

```json
{
    "status": "OK",
    "chart_data": {
        /* ChartDataModel */
    },
    "chart": "<svg>...</svg>"
}
```

---

### Subject Data

**POST** `/api/v5/subject`

Returns astrological subject data without chart rendering.

**Request:**

```json
{
    "subject": {
        /* SubjectModel */
    }
}
```

**Response:**

```json
{
    "status": "OK",
    "subject": {
        /* AstrologicalSubjectModel */
    }
}
```

---

### Natal Charts

#### Natal Chart Data

**POST** `/api/v5/chart-data/birth-chart`

Returns complete natal chart data without SVG rendering.

**Request:**

```json
{
  "subject": { /* SubjectModel */ },
  "active_points": ["Sun", "Moon", "Mercury", ...],
  "active_aspects": [{"name": "conjunction", "orb": 10}, ...],
  "distribution_method": "weighted",
  "custom_distribution_weights": {"sun": 3.0, "moon": 2.5}
}
```

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:**

```json
{
  "status": "OK",
  "chart_data": {
    "chart_type": "Natal",
    "subject": { /* AstrologicalSubjectModel */ },
    "aspects": [ /* Filtered aspects */ ],
    "element_distribution": {
      "fire": 5.0,
      "earth": 3.5,
      "air": 4.0,
      "water": 2.5,
      "fire_percentage": 33,
      "earth_percentage": 23,
      "air_percentage": 27,
      "water_percentage": 17
    },
    "quality_distribution": {
      "cardinal": 4.0,
      "fixed": 6.0,
      "mutable": 5.0,
      "cardinal_percentage": 27,
      "fixed_percentage": 40,
      "mutable_percentage": 33
    },
    "active_points": [...],
    "active_aspects": [...]
  }
}
```

#### Natal Chart with SVG

**POST** `/api/v5/chart/birth-chart`

Returns natal chart data and rendered SVG chart.

**Request:**

```json
{
  "subject": { /* SubjectModel */ },
  "theme": "classic",
  "language": "EN",
  "style": "classic",
  "show_zodiac_background_ring": true,
  "double_chart_aspect_grid_type": "list",
  "split_chart": false,
  "transparent_background": false,
  "show_house_position_comparison": true,
  "show_cusp_position_comparison": true,
  "show_degree_indicators": true,
  "show_aspect_icons": true,
  "custom_title": null,
  "active_points": [...],
  "active_aspects": [...],
  "distribution_method": "weighted",
  "custom_distribution_weights": {}
}
```

**Response:**

```json
{
    "status": "OK",
    "chart_data": {
        /* Same as chart-data endpoint */
    },
    "chart": "<svg>...</svg>"
}
```

---

### Synastry Charts

#### Synastry Chart Data

**POST** `/api/v5/chart-data/synastry`

Returns synastry comparison data between two subjects.

**Request:**

```json
{
  "first_subject": { /* SubjectModel */ },
  "second_subject": { /* SubjectModel */ },
  "include_house_comparison": true,
  "include_relationship_score": true,
  "active_points": [...],
  "active_aspects": [...],
  "distribution_method": "weighted",
  "custom_distribution_weights": {}
}
```

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:**

```json
{
  "status": "OK",
  "chart_data": {
    "chart_type": "Synastry",
    "first_subject": { /* AstrologicalSubjectModel */ },
    "second_subject": { /* AstrologicalSubjectModel */ },
    "aspects": [ /* Inter-chart aspects */ ],
    "house_comparison": {
      "first_points_in_second_houses": [...],
      "second_points_in_first_houses": [...]
    },
    "relationship_score": {
      "score_value": 18,
      "score_description": "Very Important",
      "is_destiny_sign": true,
      "score_breakdown": [
        {
          "rule": "sun_moon_conjunction",
          "description": "Sun-Moon conjunction (high precision)",
          "points": 11,
          "details": "Sun-Moon conjunction (orbit: 1.34°)"
        }
      ],
      "aspects": [...]
    },
    "element_distribution": { /* Combined distribution */ },
    "quality_distribution": { /* Combined distribution */ },
    "active_points": [...],
    "active_aspects": [...]
  }
}
```

#### Synastry Chart with SVG

**POST** `/api/v5/chart/synastry`

Returns synastry data and rendered dual-wheel chart.

**Request:** Same as `/api/v5/chart-data/synastry` plus `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`

**Response:** Same as chart-data endpoint plus `"chart": "<svg>...</svg>"` (or `"chart_wheel"` and `"chart_grid"` if split_chart=true)

---

### Transit Charts

#### Transit Chart Data

**POST** `/api/v5/chart-data/transit`

Returns transit analysis for current planetary positions affecting a natal chart.

**Request:**

```json
{
  "first_subject": { /* Natal SubjectModel */ },
  "transit_subject": {
    "name": "Transit",
    "year": 2024,
    "month": 10,
    "day": 27,
    "hour": 12,
    "minute": 0,
    "city": "London",
    "nation": "GB",
    "timezone": "Europe/London",
    "longitude": -0.1278,
    "latitude": 51.5074
  },
  "include_house_comparison": true,
  "active_points": [...],
  "active_aspects": [...],
  "distribution_method": "weighted"
}
```

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:**

```json
{
  "status": "OK",
  "chart_data": {
    "chart_type": "Transit",
    "first_subject": { /* Natal subject */ },
    "second_subject": { /* Transit subject */ },
    "aspects": [ /* Transit-to-natal aspects */ ],
    "house_comparison": {
      "first_points_in_second_houses": [...],
      "second_points_in_first_houses": [...]
    },
    "element_distribution": { /* Combined */ },
    "quality_distribution": { /* Combined */ },
    "active_points": [...],
    "active_aspects": [...]
  }
}
```

#### Transit Chart with SVG

**POST** `/api/v5/chart/transit`

Returns transit data and rendered chart.

**Request:** Same as `/api/v5/chart-data/transit` plus `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`

---

### Composite Charts

#### Composite Chart Data

**POST** `/api/v5/chart-data/composite`

Returns midpoint composite chart between two subjects.

**Request:**

```json
{
  "first_subject": { /* SubjectModel */ },
  "second_subject": { /* SubjectModel */ },
  "active_points": [...],
  "active_aspects": [...],
  "distribution_method": "weighted"
}
```

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:**

```json
{
  "status": "OK",
  "chart_data": {
    "chart_type": "Composite",
    "subject": { /* CompositeSubjectModel */ },
    "aspects": [ /* Internal composite aspects */ ],
    "element_distribution": {...},
    "quality_distribution": {...},
    "active_points": [...],
    "active_aspects": [...]
  }
}
```

#### Composite Chart with SVG

**POST** `/api/v5/chart/composite`

Returns composite data and rendered chart.

**Request:** Same as `/api/v5/chart-data/composite` plus `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`

---

### Planetary Returns

#### Solar Return Chart Data

**POST** `/api/v5/chart-data/solar-return`

Calculates solar return chart for a specific year.

**Request:**

```json
{
  "subject": { /* Natal SubjectModel */ },
  "year": 2024,
  "month": null,
  "iso_datetime": null,
  "wheel_type": "dual",
  "include_house_comparison": true,
  "return_location": {
    "city": "New York",
    "nation": "US",
    "longitude": -74.0060,
    "latitude": 40.7128,
    "timezone": "America/New_York"
  },
  "active_points": [...],
  "active_aspects": [...],
  "distribution_method": "weighted"
}
```

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:**

```json
{
  "status": "OK",
  "chart_data": {
    "chart_type": "DualReturnChart",
    "first_subject": { /* Natal subject */ },
    "second_subject": {
      "return_type": "Solar",
      /* Return chart data */
    },
    "aspects": [ /* Return-to-natal aspects */ ],
    "house_comparison": {...},
    "element_distribution": {...},
    "quality_distribution": {...}
  }
}
```

#### Solar Return Chart with SVG

**POST** `/api/v5/chart/solar-return`

Returns solar return data and rendered chart.

**Request:** Same as `/api/v5/chart-data/solar-return` plus `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`

**Response:** Adds `"return_type": "Solar"` and `"wheel_type": "dual"` or `"single"`

#### Lunar Return Chart Data

**POST** `/api/v5/chart-data/lunar-return`

Calculates lunar return chart.

**Request:** Same structure as solar return

**Note:** This endpoint does **not** accept rendering parameters (`theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`).

**Response:** Same structure with `"return_type": "Lunar"`

#### Lunar Return Chart with SVG

**POST** `/api/v5/chart/lunar-return`

Returns lunar return data and rendered chart.

**Request:** Same as `/api/v5/chart-data/lunar-return` plus `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title`

---

### Moon Phase

#### Moon Phase Details

**POST** `/api/v5/moon-phase`

Returns detailed moon phase information for a specific date/time and location. Includes phase name, illumination, waxing/waning stage, moon age, upcoming major phases, next lunar and solar eclipses, sunrise/sunset times, sun position, and zodiac signs.

**Note:** This endpoint uses a simplified request model — no `subject` wrapper, no `name`, `city`, or `nation` fields. Only date/time and geographic coordinates are required.

**Request:**

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

**Parameters:**

-   `year` (integer, required): Year of the event (1-3000).
-   `month` (integer, required): Month of the event (1-12).
-   `day` (integer, required): Day of the event (1-31).
-   `hour` (integer, required): Hour of the event (0-23).
-   `minute` (integer, required): Minute of the event (0-59).
-   `second` (integer, optional): Seconds of the event (0-59, default: 0).
-   `latitude` (float, required): Latitude of the location (-90 to 90).
-   `longitude` (float, required): Longitude of the location (-180 to 180).
-   `timezone` (string, required): IANA timezone identifier.
-   `using_default_location` (boolean, optional): Metadata flag (default: false).
-   `location_precision` (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: 0). Display rounding only — calculations use full-precision coordinates.

**Response:**

> Values are rounded for brevity. See [full example](docs/examples/moon_phase.md) for exact precision.
> Fields that may be `null` (`moonrise`, `moonset`, `position`, `visibility`, `events`, `name`, `description`, `visibility_regions`, `note`) are reserved for future expansion.

```json
{
    "status": "OK",
    "moon_phase_overview": {
        "timestamp": 750251520,
        "datestamp": "Sun, 10 Oct 1993 11:12:00 +0000",
        "sun": {
            "sunrise": 750233758,
            "sunrise_timestamp": "07:15",
            "sunset": 750273488,
            "sunset_timestamp": "18:18",
            "solar_noon": "12:47",
            "day_length": "11:02",
            "position": {
                "altitude": 31.25,
                "azimuth": 169.67,
                "distance": 149364727.19
            },
            "next_solar_eclipse": {
                "timestamp": 753227093,
                "datestamp": "Sat, 13 Nov 1993 21:44:53 +0000",
                "type": "Partial Solar Eclipse",
                "visibility_regions": null
            }
        },
        "moon": {
            "phase": 0.807,
            "phase_name": "Waning Crescent",
            "major_phase": "Last Quarter",
            "stage": "waning",
            "illumination": "32%",
            "age_days": 10,
            "lunar_cycle": "80.736%",
            "emoji": "🌘",
            "zodiac": {
                "sun_sign": "Lib",
                "moon_sign": "Leo"
            },
            "moonrise": null,
            "moonrise_timestamp": null,
            "moonset": null,
            "moonset_timestamp": null,
            "next_lunar_eclipse": {
                "timestamp": 754554366,
                "datestamp": "Mon, 29 Nov 1993 06:26:06 +0000",
                "type": "Total Lunar Eclipse",
                "visibility_regions": null
            },
            "detailed": {
                "position": null,
                "visibility": null,
                "upcoming_phases": {
                    "new_moon": {
                        "last": { "timestamp": 749415231, "datestamp": "Thu, 30 Sep 1993 18:53:51 +0000", "days_ago": 10, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 750684955, "datestamp": "Fri, 15 Oct 1993 11:35:55 +0000", "days_ago": null, "days_ahead": 5, "name": null, "description": null }
                    },
                    "first_quarter": {
                        "last": { "timestamp": 750108919, "datestamp": "Fri, 08 Oct 1993 19:35:19 +0000", "days_ago": 2, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 751279921, "datestamp": "Fri, 22 Oct 1993 08:52:01 +0000", "days_ago": null, "days_ahead": 12, "name": null, "description": null }
                    },
                    "full_moon": {
                        "last": { "timestamp": 748149015, "datestamp": "Thu, 16 Sep 1993 03:10:15 +0000", "days_ago": 24, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 751984658, "datestamp": "Sat, 30 Oct 1993 12:37:38 +0000", "days_ago": null, "days_ahead": 20, "name": null, "description": null }
                    },
                    "last_quarter": {
                        "last": { "timestamp": 748726326, "datestamp": "Wed, 22 Sep 1993 19:32:06 +0000", "days_ago": 18, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 752654150, "datestamp": "Sun, 07 Nov 1993 06:35:50 +0000", "days_ago": null, "days_ahead": 28, "name": null, "description": null }
                    }
                },
                "illumination_details": {
                    "percentage": 32.0,
                    "visible_fraction": 0.3237,
                    "phase_angle": 290.65
                }
            },
            "events": null
        },
        "location": {
            "latitude": "51.5074",
            "longitude": "-0.1276",
            "precision": 4,
            "using_default_location": false,
            "note": null
        }
    }
}
```

> **Field naming note:** `sunrise`/`sunset` are Unix timestamps (integers). `sunrise_timestamp`/`sunset_timestamp` are human-readable local time strings (HH:MM).

**Error responses (422):**

-   Missing required fields (`year`, `month`, `day`, `hour`, `minute`, `latitude`, `longitude`, `timezone`).
-   Invalid IANA timezone (e.g., `"Foo/Bar"`).
-   Out-of-range values (latitude outside -90..90, longitude outside -180..180, etc.).
-   Extra/unknown fields (e.g., `name`, `city`, `nation`). This endpoint uses strict validation.

#### Current Moon Phase (UTC)

**POST** `/api/v5/moon-phase/now-utc`

Returns detailed moon phase information for the current UTC moment at Greenwich Observatory (51.4779°N, 0.0015°W). All times in the response are in UTC.

**Request:**

```json
{}
```

All fields are optional. Defaults: `using_default_location=true`, `location_precision=0`.

**Parameters:**

-   `using_default_location` (boolean, optional): Metadata flag (default: true).
-   `location_precision` (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: 0). Display rounding only.

**Response:** Same structure as `/api/v5/moon-phase`, computed for the current UTC time at Greenwich.

**Error responses (422):**

-   Extra/unknown fields (e.g., `year`, `latitude`, `timezone`). Only `using_default_location` and `location_precision` are accepted.
-   `location_precision` outside 0-10.

---

### Relationship Score

**POST** `/api/v5/compatibility-score`

Calculates Ciro Discepolo compatibility score between two subjects.

**Request:**

```json
{
  "first_subject": { /* SubjectModel */ },
  "second_subject": { /* SubjectModel */ },
  "active_points": [...],
  "active_aspects": [...]
}
```

**Response:**

```json
{
    "status": "OK",
    "score": 11,
    "score_description": "Very Important",
    "is_destiny_sign": true,
    "score_breakdown": [
        {
            "rule": "sun_moon_conjunction",
            "description": "Sun-Moon conjunction (high precision)",
            "points": 11,
            "details": "Sun-Moon conjunction (orbit: 1.34°)"
        }
    ],
    "aspects": [
        {
            "p1_name": "Sun",
            "p2_name": "Moon",
            "aspect": "conjunction",
            "orbit": 1.34
        }
    ],
    "chart_data": {
        "chart_type": "Synastry"
        /* Full synastry data */
    }
}
```

---

## AI Context Endpoints

The API provides 10 context endpoints that parallel the chart and moon phase endpoints. Instead of returning SVG charts, these endpoints return AI-optimized context strings generated by Kerykeion's `to_context()` function, suitable for LLM consumption.

**Key Features:**

-   Non-qualitative, factual astronomical positions
-   Structured XML format optimized for AI/LLM prompts
-   Complete information including planetary positions, aspects, houses, and distributions
-   Same request parameters as corresponding chart-data endpoints

### Subject Context Endpoints

#### Subject Context

**POST** `/api/v5/context/subject`

Returns astrological subject with AI-optimized context.

**Request:** Same as `/api/v5/subject`

**Response:**

```json
{
    "status": "OK",
    "subject_context": "<chart name=\"Name\">...</chart>",
    "subject": {
        /* AstrologicalSubjectModel */
    }
}
```

#### Current Moment Context

**POST** `/api/v5/now/context`

Returns current UTC moment with AI context.

**Request:** Same as `/api/v5/now/subject`

**Response:**

```json
{
    "status": "OK",
    "subject_context": "<chart name=\"Now\">...</chart>",
    "subject": {
        /* AstrologicalSubjectModel */
    }
}
```

### Chart Context Endpoints

All chart context endpoints return structured JSON data plus AI context string.

#### Natal Context

**POST** `/api/v5/context/birth-chart`

**Request:** Same as `/api/v5/chart-data/birth-chart`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Natal\">\n  <chart name=\"Name\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* SingleChartDataModel */
    }
}
```

#### Synastry Context

**POST** `/api/v5/context/synastry`

**Request:** Same as `/api/v5/chart-data/synastry`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Synastry\">\n  <chart name=\"First\">...</chart>\n  <chart name=\"Second\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* DualChartDataModel */
    }
}
```

#### Composite Context

**POST** `/api/v5/context/composite`

**Request:** Same as `/api/v5/chart-data/composite`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Composite\">\n  <chart name=\"Composite\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* SingleChartDataModel */
    }
}
```

#### Transit Context

**POST** `/api/v5/context/transit`

**Request:** Same as `/api/v5/chart-data/transit`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Transit\">\n  <chart name=\"Natal\">...</chart>\n  <chart name=\"Transit\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* DualChartDataModel */
    }
}
```

### Return Context Endpoints

#### Solar Return Context

**POST** `/api/v5/context/solar-return`

**Request:** Same as `/api/v5/chart-data/solar-return`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"DualReturnChart\">\n  <chart name=\"Natal\">...</chart>\n  <chart name=\"Solar Return\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* ChartDataModel */
    },
    "return_type": "Solar",
    "wheel_type": "dual"
}
```

#### Lunar Return Context

**POST** `/api/v5/context/lunar-return`

**Request:** Same as `/api/v5/chart-data/lunar-return`

**Response:**

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"DualReturnChart\">\n  <chart name=\"Natal\">...</chart>\n  <chart name=\"Lunar Return\">...</chart>\n</chart_analysis>",
    "chart_data": {
        /* ChartDataModel */
    },
    "return_type": "Lunar",
    "wheel_type": "dual"
}
```

### Moon Phase Context Endpoints

#### Moon Phase Context

**POST** `/api/v5/moon-phase/context`

Returns detailed moon phase information with AI-optimized XML context. This is the context variant of `/api/v5/moon-phase`.

**Request:** Same as `/api/v5/moon-phase`

**Response:**

```json
{
    "status": "OK",
    "context": "<moon_phase_overview timestamp=\"750251520\" datestamp=\"Sun, 10 Oct 1993 11:12:00 +0000\">...</moon_phase_overview>",
    "moon_phase_overview": {
        /* MoonPhaseOverviewModel */
    }
}
```

#### Current Moon Phase Context (UTC)

**POST** `/api/v5/moon-phase/now-utc/context`

Returns current UTC moon phase at Greenwich with AI-optimized XML context. This is the context variant of `/api/v5/moon-phase/now-utc`.

**Request:** Same as `/api/v5/moon-phase/now-utc`

**Response:**

```json
{
    "status": "OK",
    "context": "<moon_phase_overview timestamp=\"...\" datestamp=\"...\">...</moon_phase_overview>",
    "moon_phase_overview": {
        /* MoonPhaseOverviewModel */
    }
}
```

### Integration with AI/LLMs

Context strings are designed for direct injection into AI prompts:

```python
import requests

response = requests.post(
    "https://astrologer.p.rapidapi.com/api/v5/context/birth-chart",
    headers={
        "X-RapidAPI-Host": "astrologer.p.rapidapi.com",
        "X-RapidAPI-Key": "YOUR_API_KEY"
    },
    json={"subject": {...}}
)

context = response.json()["context"]

prompt = f"""
You are an expert astrologer. Analyze this natal chart:

{context}

Provide insights on career potential.
"""
```

**Benefits:**

-   **No Visual Parsing**: LLMs get structured XML instead of needing to parse SVG
-   **Factual Data**: Non-qualitative, precise astronomical positions
-   **Complete Information**: All planetary positions, aspects, houses, and distributions
-   **Consistent Format**: Standardized output across all chart types

---

## Response Models

### Chart Types

-   `"Natal"` - Single subject birth chart
-   `"Synastry"` - Two-subject relationship comparison
-   `"Transit"` - Current transits to natal chart
-   `"Composite"` - Midpoint composite chart
-   `"DualReturnChart"` - Return chart with natal comparison
-   `"SingleReturnChart"` - Return chart alone

### Element Distribution Model

```json
{
    "fire": 5.0,
    "earth": 3.5,
    "air": 4.0,
    "water": 2.5,
    "fire_percentage": 33,
    "earth_percentage": 23,
    "air_percentage": 27,
    "water_percentage": 17
}
```

### Quality Distribution Model

```json
{
    "cardinal": 4.0,
    "fixed": 6.0,
    "mutable": 5.0,
    "cardinal_percentage": 27,
    "fixed_percentage": 40,
    "mutable_percentage": 33
}
```

### Aspect Model

```json
{
    "p1_name": "Sun",
    "p2_name": "Moon",
    "aspect": "conjunction",
    "orbit": 1.34,
    "aspect_degrees": 0,
    "aid": 1,
    "diff": 1.34,
    "p1": {
        /* Point details */
    },
    "p2": {
        /* Point details */
    }
}
```

---

## Distribution Methods

### Weighted (Default)

Uses traditional astrological weights:

-   Sun, Moon, Ascendant: 2.0
-   Personal planets (Mercury, Venus, Mars), Angles: 1.5
-   Social planets (Jupiter, Saturn): 1.0
-   Modern planets (Uranus, Neptune, Pluto): 0.5
-   Asteroids and TNOs: 0.3-0.4

### Pure Count

Every active point counts as exactly 1.0.

### Custom Weights

Override specific weights:

```json
{
    "distribution_method": "weighted",
    "custom_distribution_weights": {
        "sun": 3.0,
        "moon": 2.5,
        "venus": 2.0,
        "__default__": 0.75
    }
}
```

---

## Error Responses

### 400 Bad Request

```json
{
    "status": "ERROR",
    "message": "Error description"
}
```

### 422 Validation Error

```json
{
    "detail": [
        {
            "loc": ["body", "subject", "year"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### 500 Internal Server Error

```json
{
    "status": "ERROR",
    "message": "Internal server error"
}
```

---

## Rate Limits

Rate limits depend on your RapidAPI subscription tier. Check your plan details at [RapidAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing).

---

## Support

For issues or questions:

-   GitHub: [Astrologer-API](https://github.com/g-battaglia/Astrologer-API)
-   Email: kerykeion.astrology@gmail.com
-   Website: [kerykeion.net](https://www.kerykeion.net/)
