---
title: 'Astrologer API Documentation'
description: 'Explore the Astrologer API v5 documentation. A comprehensive engine for high-precision astrological calculations, SVG chart rendering, and AI-driven interpretations via RapidAPI.'
---

# Astrologer API v5 Documentation

## Overview

The **Astrologer API v5** is a comprehensive engine designed for high-precision astrological calculations, professional-grade chart rendering, and AI-driven interpretations. It serves as a robust backend for astrology applications, enabling developers to integrate complex astrological features without needing deep domain expertise.

The API provides three main capabilities:

1.  **Ephemeris Calculations**: Computes accurate positions of planets, house cusps, and other celestial points using the Swiss Ephemeris (via the [Kerykeion](https://kerykeion.net) library).
2.  **SVG Chart Generation**: Generates high-quality, ready-to-display SVG charts for various astrological techniques (Natal, Synastry, Composite, Transits, Solar/Lunar Returns, Now).
3.  **AI Context**: Leverages Generative AI to provide XML-structured explanations, syntheses, and personalized interpretations based on the calculated astrological data.

## Base URL

```
https://astrologer.p.rapidapi.com/api/v5
```

All endpoints are prefixed with `/api/v5`.

## Authentication

The API is served through [RapidAPI](https://rapidapi.com). Every request must include two headers:

| Header | Description |
|--------|-------------|
| `X-RapidAPI-Key` | Your personal RapidAPI application key. |
| `X-RapidAPI-Host` | `astrologer.p.rapidapi.com` |

You can obtain an API key by subscribing to the Astrologer API on the [RapidAPI marketplace](https://rapidapi.com).

**Example request:**

```bash
curl -X POST "https://astrologer.p.rapidapi.com/api/v5/subject" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: astrologer.p.rapidapi.com" \
  -d '{ "subject": { "name": "John", "year": 1990, "month": 1, "day": 15, "hour": 12, "minute": 30, "city": "London", "nation": "GB", "longitude": -0.1276, "latitude": 51.5074, "timezone": "Europe/London" } }'
```

## Core Concepts

### The "Subject"

The fundamental unit of the API is the **Subject**. A Subject represents a specific entity (person, event, or moment) defined by a time and a location on Earth. Almost every endpoint requires one or more `subject` objects to perform calculations.

#### Subject Object Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Display name for the subject. |
| `year` | integer | Yes | - | Year (1-3000). |
| `month` | integer | Yes | - | Month (1-12). |
| `day` | integer | Yes | - | Day (1-31). |
| `hour` | integer | Yes | - | Hour (0-23). |
| `minute` | integer | Yes | - | Minute (0-59). |
| `second` | integer | No | `0` | Seconds (0-59). |
| `city` | string | Yes | - | City name associated with the event. |
| `nation` | string | No | `null` | Two-letter ISO 3166-1 alpha-2 country code (e.g. `"GB"`, `"US"`, `"IT"`). |
| `longitude` | float | Conditional | `null` | Longitude (-180 to 180). Required unless `geonames_username` is provided. |
| `latitude` | float | Conditional | `null` | Latitude (-90 to 90). Required unless `geonames_username` is provided. |
| `timezone` | string | Conditional | `null` | IANA timezone identifier (e.g. `"Europe/London"`). Required unless `geonames_username` is provided. |
| `altitude` | float | No | `null` | Altitude above sea level in meters. |
| `is_dst` | boolean | No | `null` | Override automatic daylight saving time detection. |
| `geonames_username` | string | No | `null` | GeoNames username to resolve location from city/nation. When provided, `latitude`, `longitude`, and `timezone` are ignored. Create a free username at [geonames.org](https://www.geonames.org/login/). |
| `zodiac_type` | string | No | `"Tropical"` | `"Tropical"` or `"Sidereal"`. |
| `sidereal_mode` | string | No | `null` | Ayanamsa system. Required when `zodiac_type` is `"Sidereal"`. See [Sidereal Modes](#sidereal-modes). |
| `perspective_type` | string | No | `"Apparent Geocentric"` | Astronomical perspective. See [Perspective Types](#perspective-types). |
| `houses_system_identifier` | string | No | `"P"` | House system code. See [House Systems](#house-systems). |
| `custom_ayanamsa_t0` | float | No | `null` | Julian Day of the reference epoch for the `USER` sidereal mode. |
| `custom_ayanamsa_ayan_t0` | float | No | `null` | Ayanamsa offset in degrees at the reference epoch. Required with `custom_ayanamsa_t0` when `sidereal_mode` is `"USER"`. |

**Location resolution**: You must provide location in one of two ways:

1. **Coordinates** (offline, recommended): Supply all three of `latitude`, `longitude`, and `timezone`.
2. **GeoNames** (online): Supply `geonames_username` with `city` and `nation`. The API resolves coordinates automatically. If both are provided, GeoNames takes priority and coordinates are cleared.

#### Transit Subject

Transit endpoints use a simplified subject model (`transit_subject`) that does **not** include `zodiac_type`, `sidereal_mode`, `perspective_type`, or `houses_system_identifier`. These settings are inherited from the natal `first_subject`. The `name` field defaults to `"Transit"`.

### Chart Types

The API supports the following chart types:

-   **Natal Chart**: A map of the sky at a single moment (e.g., a birth).
-   **Now Chart**: A natal chart for the current UTC moment at Greenwich Observatory.
-   **Synastry Chart**: A bi-wheel chart comparing two subjects to analyze their relationship dynamics.
-   **Composite Chart**: A single-wheel chart derived from the midpoints of two subjects, representing the relationship as a third entity.
-   **Transit Chart**: A bi-wheel chart comparing a natal subject with a transit moment to forecast trends.
-   **Solar/Lunar Returns**: Charts calculated for the moment the Sun or Moon returns to its exact natal position.

## Computation Options

All data, chart, and context endpoints that compute chart data accept these optional configuration fields at the request body root level (not inside `subject`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `active_points` | array of strings | Default preset (18 points) | Override which celestial points are included. See [Active Points](#active-points). Accepts case-insensitive names and aliases (e.g. `"asc"` for `"Ascendant"`, `"lilith"` for `"Mean_Lilith"`). |
| `active_aspects` | array of objects | Default preset (6 aspects) | Override which aspects are calculated and their orbs. Each object: `{"name": "conjunction", "orb": 10}`. See [Active Aspects](#active-aspects). |
| `distribution_method` | string | `"weighted"` | Element/quality distribution strategy: `"weighted"` (default, planets have different weights) or `"pure_count"` (each point counts equally). |
| `custom_distribution_weights` | object | `null` | Custom weights map when using `"weighted"` distribution. Keys are lowercase point names (e.g. `"sun"`, `"moon"`, `"ascendant"`), values are floats. |

## Rendering Options

Chart (SVG) endpoints additionally accept these rendering fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `theme` | string | `"classic"` | Visual theme. See [Themes](#themes). |
| `language` | string | `"EN"` | Language for chart labels. See [Languages](#languages). |
| `style` | string | `"classic"` | `"classic"` (traditional wheel) or `"modern"` (concentric rings). |
| `split_chart` | boolean | `false` | When `true`, returns separate `chart_wheel` and `chart_grid` SVG strings instead of a single `chart` string. |
| `transparent_background` | boolean | `false` | Render chart with transparent background. |
| `custom_title` | string | `null` | Override the chart title (max 40 characters). |
| `show_house_position_comparison` | boolean | `true` | Show the house comparison table. |
| `show_cusp_position_comparison` | boolean | `true` | Show cusp position comparison table (dual charts). |
| `show_degree_indicators` | boolean | `true` | Show radial lines and degree numbers for planet positions. |
| `show_aspect_icons` | boolean | `true` | Show aspect icons on aspect lines. |
| `show_zodiac_background_ring` | boolean | `true` | Show colored zodiac sign wedges (only affects `"modern"` style). |
| `double_chart_aspect_grid_type` | string | `"list"` | Aspect display layout for dual charts: `"list"` (vertical) or `"table"` (grid matrix). |

## Error Handling

The API uses standard HTTP status codes:

-   **200 OK**: Success.
-   **400 Bad Request**: Invalid request parameters or Kerykeion calculation error.
-   **422 Unprocessable Entity**: Validation error (e.g., invalid date, missing required field, invalid timezone).
-   **500 Internal Server Error**: Unexpected server error.

**Error response body:**

All error responses return JSON with the following structure:

```json
{
  "status": "ERROR",
  "message": "Descriptive error message explaining what went wrong.",
  "error_type": "ValueError"
}
```

**GeoNames-specific errors** (city/nation resolution failures) return a standardized message with instructions:

```json
{
  "status": "ERROR",
  "message": "City/Nation name error or invalid GeoNames username. Please check your username or city name and try again. You can create a free username here: https://www.geonames.org/login/. If you want to bypass the usage of GeoNames, please remove the geonames_username field from the request. Note: The nation field should be the country code (e.g. US, UK, FR, DE, etc.)."
}
```

## Configuration Reference

### Themes

| Value | Description |
|-------|-------------|
| `"classic"` | Traditional astrology colors (default). |
| `"light"` | Light background theme. |
| `"dark"` | Dark background theme. |
| `"dark-high-contrast"` | Dark background with high contrast colors. |
| `"strawberry"` | Warm pink/red tones. |
| `"black-and-white"` | Monochrome. |

### Languages

| Code | Language |
|------|----------|
| `"EN"` | English (default) |
| `"FR"` | French |
| `"PT"` | Portuguese |
| `"IT"` | Italian |
| `"CN"` | Chinese |
| `"ES"` | Spanish |
| `"RU"` | Russian |
| `"TR"` | Turkish |
| `"DE"` | German |
| `"HI"` | Hindi |

### House Systems

| Code | House System |
|------|-------------|
| `"P"` | **Placidus** (default, most common in Western astrology) |
| `"K"` | Koch |
| `"W"` | Whole Sign |
| `"A"` | Equal |
| `"B"` | Alcabitius |
| `"C"` | Campanus |
| `"D"` | Equal (MC) |
| `"F"` | Carter Poli-Equatorial |
| `"H"` | Horizon / Azimuth |
| `"I"` | Sunshine |
| `"i"` | Sunshine (alternative) |
| `"L"` | Pullen SD |
| `"M"` | Morinus |
| `"N"` | Equal / 1=Aries |
| `"O"` | Porphyry |
| `"Q"` | Pullen SR |
| `"R"` | Regiomontanus |
| `"S"` | Sripati |
| `"T"` | Polich/Page (Topocentric) |
| `"U"` | Krusinski-Pisa-Goelzer |
| `"V"` | Equal / Vehlow |
| `"X"` | Axial Rotation / Meridian |
| `"Y"` | APC |

### Perspective Types

| Value | Description |
|-------|-------------|
| `"Apparent Geocentric"` | Earth-centered with atmospheric refraction correction (default). |
| `"True Geocentric"` | Earth-centered without refraction correction. |
| `"Heliocentric"` | Sun-centered view. |
| `"Topocentric"` | Observer's surface location with parallax correction. |

### Sidereal Modes

Required when `zodiac_type` is `"Sidereal"`. 48 modes available:

**Indian / Vedic:**
`LAHIRI`, `LAHIRI_1940`, `LAHIRI_ICRC`, `LAHIRI_VP285`, `KRISHNAMURTI`, `KRISHNAMURTI_VP291`, `RAMAN`, `USHASHASHI`, `JN_BHASIN`, `YUKTESHWAR`, `ARYABHATA`, `ARYABHATA_522`, `ARYABHATA_MSUN`, `SURYASIDDHANTA`, `SURYASIDDHANTA_MSUN`, `SS_CITRA`, `SS_REVATI`, `TRUE_CITRA`, `TRUE_MULA`, `TRUE_PUSHYA`, `TRUE_REVATI`, `TRUE_SHEORAN`

**Western Sidereal:**
`FAGAN_BRADLEY`, `DELUCE`, `DJWHAL_KHUL`, `HIPPARCHOS`, `SASSANIAN`

**Babylonian:**
`BABYL_KUGLER1`, `BABYL_KUGLER2`, `BABYL_KUGLER3`, `BABYL_HUBER`, `BABYL_ETPSC`, `BABYL_BRITTON`

**Galactic Alignment:**
`GALCENT_0SAG`, `GALCENT_COCHRANE`, `GALCENT_MULA_WILHELM`, `GALCENT_RGILBRAND`, `GALEQU_FIORENZA`, `GALEQU_IAU1958`, `GALEQU_MULA`, `GALEQU_TRUE`, `GALALIGN_MARDYKS`

**Reference Frames:**
`J2000`, `J1900`, `B1950`

**Astronomical:**
`ALDEBARAN_15TAU`, `VALENS_MOON`

**User-Defined:**
`USER` -- Requires `custom_ayanamsa_t0` (Julian Day of reference epoch) and `custom_ayanamsa_ayan_t0` (ayanamsa offset in degrees at that epoch).

### Active Points

The default preset includes 18 points. You can override with any combination of the 63 available points:

**Planets (10):** `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, `Pluto`

**Lunar Nodes (4):** `Mean_North_Lunar_Node`, `True_North_Lunar_Node`, `Mean_South_Lunar_Node`, `True_South_Lunar_Node`

**Special Points (5):** `Chiron`, `Mean_Lilith`, `True_Lilith`, `Earth`, `Pholus`

**Asteroids (4):** `Ceres`, `Pallas`, `Juno`, `Vesta`

**Trans-Neptunian Objects (7):** `Eris`, `Sedna`, `Haumea`, `Makemake`, `Ixion`, `Orcus`, `Quaoar`

**Fixed Stars (23):** `Regulus`, `Spica`, `Aldebaran`, `Antares`, `Sirius`, `Fomalhaut`, `Algol`, `Betelgeuse`, `Canopus`, `Procyon`, `Arcturus`, `Pollux`, `Deneb`, `Altair`, `Rigel`, `Achernar`, `Capella`, `Vega`, `Alcyone`, `Alphecca`, `Algorab`, `Deneb_Algedi`, `Alkaid`

**Arabic Parts (4):** `Pars_Fortunae`, `Pars_Spiritus`, `Pars_Amoris`, `Pars_Fidei`

**Angular Points (6):** `Ascendant`, `Medium_Coeli`, `Descendant`, `Imum_Coeli`, `Vertex`, `Anti_Vertex`

**Accepted aliases** (case-insensitive): `asc` = `Ascendant`, `mc` = `Medium_Coeli`, `ic` = `Imum_Coeli`, `desc` = `Descendant`, `lilith` = `Mean_Lilith`, `north_node` = `Mean_North_Lunar_Node`, `south_node` = `Mean_South_Lunar_Node`, `mean_node` = `Mean_North_Lunar_Node`, `true_node` = `True_North_Lunar_Node`, `mean_south_node` = `Mean_South_Lunar_Node`, `true_south_node` = `True_South_Lunar_Node`

### Active Aspects

The default preset includes 6 aspects. All 11 are available:

| Aspect | Degrees | Default Orb | Active by Default |
|--------|---------|-------------|-------------------|
| `conjunction` | 0 | 10 | Yes |
| `opposition` | 180 | 10 | Yes |
| `trine` | 120 | 8 | Yes |
| `sextile` | 60 | 6 | Yes |
| `square` | 90 | 5 | Yes |
| `quintile` | 72 | 1 | Yes |
| `semi-sextile` | 30 | 1 | No |
| `semi-square` | 45 | 1 | No |
| `sesquiquadrate` | 135 | 1 | No |
| `biquintile` | 144 | 1 | No |
| `quincunx` | 150 | 1 | No |

**Note:** Aspect names are **lowercase** in both request and response payloads.

### Sign Abbreviations

Response payloads use three-letter abbreviations for zodiac signs:

| Abbreviation | Sign | `sign_num` |
|-------------|------|------------|
| `Ari` | Aries | 0 |
| `Tau` | Taurus | 1 |
| `Gem` | Gemini | 2 |
| `Can` | Cancer | 3 |
| `Leo` | Leo | 4 |
| `Vir` | Virgo | 5 |
| `Lib` | Libra | 6 |
| `Sco` | Scorpio | 7 |
| `Sag` | Sagittarius | 8 |
| `Cap` | Capricorn | 9 |
| `Aqu` | Aquarius | 10 |
| `Pis` | Pisces | 11 |

## Response Key Naming

Most context endpoints return the AI text in a field called `context`. Two exceptions use `subject_context` instead:

- `POST /api/v5/context/subject` -- returns `subject_context` + `subject`
- `POST /api/v5/now/context` -- returns `subject_context` + `subject`

All other context endpoints return `context` + `chart_data`.

## Documentation Index

> **[Browse All Examples](examples/README.md)** — Complete categorized index of all endpoint examples with chart previews.

### Data Endpoints (JSON)

Endpoints that return raw calculated data (JSON) without visual charts. Ideal for custom frontend rendering or data analysis.

-   [**Subject**](data/subject.md) ([Example](examples/subject.md)): Calculate a subject's astrological data.
-   [**Now Subject**](data/now_subject.md) ([Example](examples/now_subject.md)): Get the astrological data for the current moment.
-   [**Compatibility Score**](data/compatibility_score.md) ([Example](examples/compatibility_score.md)): Calculate a numerical compatibility score between two people.
-   **Chart Data:**
    -   [Natal Chart Data](data/chart_data_natal.md) ([Example](examples/natal_chart_data.md))
    -   [Synastry Chart Data](data/chart_data_synastry.md) ([Example](examples/synastry_chart_data.md))
    -   [Composite Chart Data](data/chart_data_composite.md) ([Example](examples/composite_chart_data.md))
    -   [Transit Chart Data](data/chart_data_transit.md) ([Example](examples/transit_chart_data.md))
    -   [Solar Return Data](data/chart_data_solar_return.md) ([Example](examples/solar_return_chart_data.md))
    -   [Lunar Return Data](data/chart_data_lunar_return.md) ([Example](examples/lunar_return_chart_data.md))

### Moon Phase Endpoints

Dedicated endpoints for detailed lunar phase analysis, using a simplified request model (no `subject` wrapper).

-   [**Moon Phase**](data/moon_phase.md) ([Example](examples/moon_phase.md)): Detailed moon phase for a specific date/time and location.
-   [**Moon Phase Now (UTC)**](data/moon_phase_now_utc.md) ([Example](examples/moon_phase_now_utc.md)): Current moon phase at Greenwich.
-   [**Moon Phase Context**](context/moon_phase_context.md) ([Example](examples/moon_phase_context.md)): Moon phase with AI-optimized XML context.
-   [**Moon Phase Now Context (UTC)**](context/moon_phase_now_utc_context.md) ([Example](examples/moon_phase_now_utc_context.md)): Current moon phase with AI-optimized XML context.

### Chart Endpoints (SVG)

Endpoints that return rendered SVG charts along with the calculation data.

-   [**Natal Chart**](charts/natal_chart.md) ([Example](examples/natal_chart_svg.md))
-   [**Now Chart**](charts/now_chart.md) ([Example](examples/now_chart_svg.md))
-   [**Synastry Chart**](charts/synastry_chart.md) ([Example](examples/synastry_chart_svg.md))
-   [**Composite Chart**](charts/composite_chart.md) ([Example](examples/composite_chart_svg.md))
-   [**Transit Chart**](charts/transit_chart.md) ([Example](examples/transit_chart_svg.md))
-   [**Solar Return Chart**](charts/solar_return_chart.md) ([Example](examples/solar_return_chart_svg.md))
-   [**Lunar Return Chart**](charts/lunar_return_chart.md) ([Example](examples/lunar_return_chart_svg.md))

### Context Endpoints (AI)

Endpoints that return AI-optimized XML interpretations and context.

-   [**Subject Context**](context/subject_context.md) ([Example](examples/subject_context.md))
-   [**Now Context**](context/now_context.md) ([Example](examples/now_context.md))
-   [**Natal Chart Context**](context/natal_context.md) ([Example](examples/natal_context.md))
-   [**Synastry Context**](context/synastry_context.md) ([Example](examples/synastry_context.md))
-   [**Composite Context**](context/composite_context.md) ([Example](examples/composite_context.md))
-   [**Transit Context**](context/transit_context.md) ([Example](examples/transit_context.md))
-   [**Solar Return Context**](context/solar_return_context.md) ([Example](examples/solar_return_context.md))
-   [**Lunar Return Context**](context/lunar_return_context.md) ([Example](examples/lunar_return_context.md))

---

_Powered by [Kerykeion](https://kerykeion.net) -- the open-source Python astrology library._
