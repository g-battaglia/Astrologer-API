# Astrologer API

Astrologer API lets you add **professional-grade astrology features** to any app — fast.  
It delivers **plug-and-play SVG charts**, **rich astrological data**, and **AI-optimized XML context** for natal, synastry, transits, composites, returns, and moon phases.

-   NASA-grade astronomical accuracy
-   Production-ready JSON + beautiful SVGs
-   Used in astrology apps, compatibility/dating systems, dashboards and SaaS tools

Chart examples:

<table>
  <tr>
    <td align="center"><strong>Classic Default</strong></td>
    <td align="center"><strong>Classic Dark</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Natal%20Chart.svg" width="450" alt="Classic Default Natal Chart"></td>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart.svg" width="450" alt="Classic Dark Natal Chart"></td>
  </tr>
  <tr>
    <td align="center"><strong>Modern Default</strong></td>
    <td align="center"><strong>Modern Dark</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern.svg" width="450" alt="Modern Default Natal Chart"></td>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart%20-%20Modern.svg" width="450" alt="Modern Dark Natal Chart"></td>
  </tr>
</table>

👉 Ready to use it? Subscribe on RapidAPI: <a href="https://www.kerykeion.net/astrologer-api/subscribe" target="_blank">https://www.kerykeion.net/astrologer-api/subscribe</a>

## Quick start

Every request must include your RapidAPI key.

Headers:

```javascript
{
    'X-RapidAPI-Host': 'astrologer.p.rapidapi.com',
    'X-RapidAPI-Key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
}
```

Minimal birth chart request (SVG + data):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/birth-chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "subject": {
            "name": "John Doe",
            "year": 1980,
            "month": 12,
            "day": 12,
            "hour": 12,
            "minute": 12,
            "longitude": 0,
            "latitude": 51.4825766,
            "timezone": "Europe/London"
        },
        "theme": "dark"
    }'
```

Response shape:

```json
{
    "status": "OK",
    "chart": "<svg>...</svg>", // The rendered SVG chart is returned here as a string
    "chart_data": {
        /* aspects, houses, distributions, subjects */
    }
}
```

Prefer separate SVGs? Use "split_chart": true. You'll receive chart_wheel and chart_grid instead of chart. See the split example below.

NOTE: The rendered SVG chart is returned in the `chart` key of the JSON response.

## Endpoints

### Chart Endpoints (SVG charts + data)

The API provides chart endpoints that return rendered SVG charts (found in the `chart` key) together with full astrological data.

-   `/api/v5/chart/birth-chart` (POST) - Natal chart SVG + data
-   `/api/v5/chart/synastry` (POST) - Synastry chart SVG + combined data
-   `/api/v5/chart/transit` (POST) - Transit chart SVG + natal and transit data
-   `/api/v5/chart/composite` (POST) - Composite chart SVG + midpoint data
-   `/api/v5/chart/solar-return` (POST) - Solar return chart SVG + data
-   `/api/v5/chart/lunar-return` (POST) - Lunar return chart SVG + data
-   `/api/v5/now/chart` (POST) - Current moment chart SVG + data

### Data Endpoints (JSON only, no SVG)

Use these endpoints when you only need structured astrological data without rendered charts.

-   `/api/v5/chart-data/birth-chart` (POST) - Natal chart data only
-   `/api/v5/chart-data/synastry` (POST) - Synastry data only
-   `/api/v5/chart-data/transit` (POST) - Transit data only
-   `/api/v5/chart-data/composite` (POST) - Composite data only
-   `/api/v5/chart-data/solar-return` (POST) - Solar return data only
-   `/api/v5/chart-data/lunar-return` (POST) - Lunar return data only
-   `/api/v5/subject` (POST) - Normalized subject object only
-   `/api/v5/now/subject` (POST) - Current UTC subject data
-   `/api/v5/compatibility-score` (POST) - Ciro Discepolo compatibility score + summary

### Moon Phase Endpoints

Dedicated endpoints for detailed lunar phase analysis. These use a simplified request model (no `subject` wrapper — just date/time and coordinates).

-   `/api/v5/moon-phase` (POST) - Detailed moon phase for a specific date/time and location
-   `/api/v5/moon-phase/now-utc` (POST) - Current moon phase at Greenwich (UTC)
-   `/api/v5/moon-phase/context` (POST) - Moon phase data with AI-optimized XML context
-   `/api/v5/moon-phase/now-utc/context` (POST) - Current moon phase with AI-optimized XML context

### Context Endpoints (AI/LLM Integration)

The API provides AI-optimized context endpoints that return structured XML descriptions instead of SVG charts. These are designed for LLM integration and AI applications:

-   `/api/v5/context/subject` (POST) - Subject data with AI context
-   `/api/v5/context/birth-chart` (POST) - Natal chart data with AI context
-   `/api/v5/context/synastry` (POST) - Synastry data with AI context
-   `/api/v5/context/composite` (POST) - Composite data with AI context
-   `/api/v5/context/transit` (POST) - Transit data with AI context
-   `/api/v5/context/solar-return` (POST) - Solar return data with AI context
-   `/api/v5/context/lunar-return` (POST) - Lunar return data with AI context
-   `/api/v5/now/context` (POST) - Current moment with AI context

These endpoints accept the same parameters as their corresponding chart-data endpoints but return `context` (AI-optimized XML context string) instead of SVG charts.

## Documentation

-   <a href="https://www.kerykeion.net/astrologer-api-swagger/" target="_blank">Swagger OpenAPI (interactive)</a>
-   <a href="https://www.kerykeion.net/astrologer-api-redoc/" target="_blank">Redoc OpenAPI (reference)</a>
-   <a href="https://www.kerykeion.net/content/astrologer-api/" target="_blank">Full Documentation</a>

## Copy‑paste examples

### 1) Natal chart (SVG + data)

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/birth-chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "subject": { "name": "Ada", "year": 1990, "month": 5, "day": 1, "hour": 10, "minute": 0, "longitude": 12.4964, "latitude": 41.9028, "timezone": "Europe/Rome" },
        "theme": "light",
        "language": "EN"
    }'
```

Two SVGs (wheel + grid) with split_chart:

-   When you add "split_chart": true, the response does not include the single "chart" key.
-   Instead you get two SVGs:
    -   chart_wheel: the zodiac wheel (signs, houses, degrees, glyphs)
    -   chart_grid: the aspect grid/table and legend
-   Useful when you need separate positioning, animation, or different sizes for wheel and grid.
-   Works with all /charts/\* endpoints and can be combined with transparent_background.

Request:

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/birth-chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "subject": { "name": "Ada", "year": 1990, "month": 5, "day": 1, "hour": 10, "minute": 0, "longitude": 12.4964, "latitude": 41.9028, "timezone": "Europe/Rome" },
        "split_chart": true
    }'
```

Response (shape):

```json
{
    "status": "OK",
    "chart_wheel": "<svg>...</svg>",
    "chart_grid": "<svg>...</svg>",
    "chart_data": {
        /* ... */
    }
}
```

Make the SVG background transparent:

```bash
... -d '{ "subject": { /* as above */ }, "transparent_background": true }'
```

Data‑only variant:

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart-data/birth-chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{ "subject": { "name": "Ada", "year": 1990, "month": 5, "day": 1, "hour": 10, "minute": 0, "longitude": 12.4964, "latitude": 41.9028, "timezone": "Europe/Rome" } }'
```

### 2) Synastry chart

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/synastry' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "first_subject": { "name": "Alice", "year": 1990, "month": 7, "day": 5, "hour": 9, "minute": 30, "longitude": -0.1278, "latitude": 51.5074, "timezone": "Europe/London" },
        "second_subject": { "name": "Bob", "year": 1988, "month": 1, "day": 20, "hour": 18, "minute": 15, "longitude": 2.3522, "latitude": 48.8566, "timezone": "Europe/Paris" },
        "theme": "dark"
    }'
```

Compatibility score only (fast):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/compatibility-score' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "first_subject": { /* as above */ },
        "second_subject": { /* as above */ }
    }'
```

### 3) Transits (now or custom moment)

Current time (simple POST):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/now/chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{}'
```

Transit for a natal subject at a chosen moment:

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/transit' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "first_subject": { /* natal subject */ },
        "transit_subject": { "name": "Transit", "year": 2025, "month": 1, "day": 1, "hour": 0, "minute": 0, "city": "London", "nation": "GB", "longitude": 0, "latitude": 51.48, "timezone": "Europe/London" }
    }'
```

### 4) Solar return

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/chart/solar-return' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "subject": { /* natal */ },
        "year": 2025,
        "wheel_type": "dual",
        "return_location": { "longitude": -74.0060, "latitude": 40.7128, "timezone": "America/New_York" }
    }'
```

### 5) Moon phase

Get detailed lunar phase info (no `subject` wrapper needed):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/moon-phase' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "year": 1993, "month": 10, "day": 10, "hour": 12, "minute": 12,
        "latitude": 51.5074, "longitude": -0.1276, "timezone": "Europe/London"
    }'
```

Response (shape):

```json
{
    "status": "OK",
    "moon_phase_overview": {
        "timestamp": 750251520,
        "datestamp": "Sun, 10 Oct 1993 11:12:00 +0000",
        "sun": { "sunrise_timestamp": "07:15", "sunset_timestamp": "18:18", "solar_noon": "12:47", "..." : "..." },
        "moon": { "phase": 0.807, "phase_name": "Waning Crescent", "illumination": "32%", "emoji": "🌘", "..." : "..." },
        "location": { "latitude": "52", "longitude": "0", "precision": 0 }
    }
}
```

Current moon phase (empty body):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/moon-phase/now-utc' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{}'
```

Moon phase with AI context (same request, XML context added):

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/moon-phase/context' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "year": 1993, "month": 10, "day": 10, "hour": 12, "minute": 12,
        "latitude": 51.5074, "longitude": -0.1276, "timezone": "Europe/London"
    }'
```

### 6) AI Context (for LLM integration)

Every chart type has a matching `/context/` endpoint that returns an XML context string instead of SVG. Use it to feed astrological data directly into an LLM prompt:

```bash
curl -X POST 'https://astrologer.p.rapidapi.com/api/v5/context/birth-chart' \
    -H 'Content-Type: application/json' \
    -H 'X-RapidAPI-Host: astrologer.p.rapidapi.com' \
    -H 'X-RapidAPI-Key: YOUR_API_KEY' \
    -d '{
        "subject": { "name": "Ada", "year": 1990, "month": 5, "day": 1, "hour": 10, "minute": 0, "longitude": 12.4964, "latitude": 41.9028, "timezone": "Europe/Rome" }
    }'
```

Response (shape):

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Natal\">...\n</chart_analysis>",
    "chart_data": {
        /* same structure as /chart-data/birth-chart */
    }
}
```

The `context` string is structured XML with planetary positions, aspects, houses, and distributions — ready to inject into any AI prompt. Available for all chart types, subject, now, and moon phase.

## Options at a glance

There are two kinds of options:

-   Computation options (work everywhere, including /chart-data/\*):

    -   active_points, active_aspects
    -   distribution_method: "weighted" (default) or "pure_count"
    -   custom_distribution_weights: override weights selectively

-   Rendering options (only for /charts/\* endpoints):
    -   theme: light, dark, dark-high-contrast, classic, strawberry, black-and-white
    -   language: EN, FR, PT, ES, TR, RU, IT, CN, DE, HI
    -   style: "classic" (default) or "modern" — selects the chart wheel layout
    -   show_zodiac_background_ring: true (default) — colored zodiac wedges behind the wheel (modern style only)
    -   double_chart_aspect_grid_type: "list" (default) or "table" — aspect display format for dual charts
    -   split_chart: true to receive wheel and grid separately
    -   transparent_background: true for transparent SVG background
    -   show_house_position_comparison: false hides the house comparison table and widens the SVG layout
    -   show_cusp_position_comparison: false hides cusp comparison grids on dual charts (Synastry, Transit dual wheels, DualReturnChart)
    -   show_degree_indicators: false hides radial lines and degree numbers around the wheel (single and dual charts)
    -   show_aspect_icons: false hides aspect icons on aspect lines
    -   custom_title: short (≤40 chars) override for the title printed on the chart

Quick example with custom weights:

```json
{
    "distribution_method": "weighted",
    "custom_distribution_weights": {
        "sun": 2.0,
        "moon": 2.0,
        "ascendant": 2.0,
        "medium_coeli": 1.5,
        "mercury": 1.5,
        "venus": 1.5,
        "mars": 1.5,
        "jupiter": 1.0,
        "saturn": 1.0
    }
}
```

For full lists of points/aspects/themes and defaults, see the docs below.

## Languages

Localize chart labels and texts by setting the language parameter (default: EN).

Supported codes:

-   EN (English)
-   FR (French)
-   PT (Portuguese)
-   ES (Spanish)
-   TR (Turkish)
-   RU (Russian)
-   IT (Italian)
-   CN (Chinese)
-   DE (German)
-   HI (Hindi)

Example:

```json
{
    "subject": {
        /* ... */
    },
    "language": "RU"
}
```

## Transparent background

Render charts without a background fill so you can overlay them on any design. Works with any theme and across all /charts/\* endpoints. Can be combined with split_chart.

Example:

```json
{
    "subject": {
        /* ... */
    },
    "theme": "dark",
    "transparent_background": true
}
```

## Hide comparison tables and degree indicators

On single-wheel charts the default layout includes the house comparison table. Set `show_house_position_comparison` to `false` to hide that panel and allow the SVG to use the extra width.

On dual charts (Synastry, Transit dual wheels, DualReturnChart) the API also renders cusp comparison grids by default. Set `show_cusp_position_comparison` to `false` to hide those tables while keeping the wheel.

All chart types now display radial lines and degree numbers for planet positions; you can turn them off with `show_degree_indicators: false` for a cleaner look.

```json
{
    "subject": {
        /* ... */
    },
    "show_house_position_comparison": false,
    "show_cusp_position_comparison": false,
    "show_degree_indicators": false
}
```

## Custom chart titles

Provide a short (`<= 40` chars) `custom_title` to override the text rendered above the chart for that single request. Whitespace is trimmed and empty strings are ignored.

```json
{
    "subject": {
        /* ... */
    },
    "custom_title": "Alice & Bob (Q1 2025)"
}
```

## Chart style (Classic vs Modern)

Choose between two chart wheel layouts using the `style` parameter (default: `"classic"`):

- `"classic"` — traditional concentric wheel with houses and planets
- `"modern"` — concentric ring layout with a contemporary aesthetic

<table>
  <tr>
    <td align="center"><strong>Modern Natal (Default)</strong></td>
    <td align="center"><strong>Modern Natal (Dark)</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Natal%20Chart%20-%20Modern.svg" width="450" alt="Modern Default Natal Chart"></td>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart%20-%20Modern.svg" width="450" alt="Modern Dark Natal Chart"></td>
  </tr>
  <tr>
    <td align="center"><strong>Modern Synastry (Default)</strong></td>
    <td align="center"><strong>Modern Synastry (Dark)</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Synastry%20Chart%20-%20Modern.svg" width="450" alt="Modern Default Synastry Chart"></td>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Dark%20Theme%20Synastry%20-%20Synastry%20Chart%20-%20Modern.svg" width="450" alt="Modern Dark Synastry Chart"></td>
  </tr>
  <tr>
    <td align="center"><strong>Modern Transit (Default)</strong></td>
    <td align="center"><strong>Modern Transit (Dark)</strong></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Transit%20Chart%20-%20Modern.svg" width="450" alt="Modern Default Transit Chart"></td>
    <td><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20-%20Dark%20Theme%20Transit%20-%20Transit%20Chart%20-%20Modern.svg" width="450" alt="Modern Dark Transit Chart"></td>
  </tr>
</table>

When using `"modern"`, you can also control the colored zodiac wedges behind the wheel with `show_zodiac_background_ring` (default: `true`).

For dual charts (synastry, transit, composite, returns), you can choose how aspects are displayed with `double_chart_aspect_grid_type`:

- `"list"` (default) — vertical list of aspects
- `"table"` — grid/matrix table of aspects

```json
{
    "subject": { /* ... */ },
    "style": "modern",
    "show_zodiac_background_ring": true,
    "theme": "dark"
}
```

Dual chart with table aspect grid:

```json
{
    "first_subject": { /* ... */ },
    "second_subject": { /* ... */ },
    "double_chart_aspect_grid_type": "table"
}
```

## Zodiac types (Tropical vs Sidereal)

Choose the zodiac in the subject object:

-   zodiac_type: "Tropical" (default) or "Sidereal"
-   If "Sidereal", also set sidereal_mode (ayanamsha)

Supported sidereal_mode values (47 named modes + USER, 48 total):

-   **Indian / Vedic:** FAGAN_BRADLEY, LAHIRI, LAHIRI_1940, LAHIRI_ICRC, LAHIRI_VP285, DELUCE, RAMAN, USHASHASHI, KRISHNAMURTI, KRISHNAMURTI_VP291, DJWHAL_KHUL, YUKTESHWAR, JN_BHASIN, ARYABHATA, ARYABHATA_522, ARYABHATA_MSUN, SURYASIDDHANTA, SURYASIDDHANTA_MSUN, SS_CITRA, SS_REVATI
-   **Galactic center / equator:** GALCENT_0SAG, GALCENT_COCHRANE, GALCENT_MULA_WILHELM, GALCENT_RGILBRAND, GALEQU_FIORENZA, GALEQU_IAU1958, GALEQU_MULA, GALEQU_TRUE, GALALIGN_MARDYKS
-   **True star / nakshatra:** TRUE_CITRA, TRUE_MULA, TRUE_PUSHYA, TRUE_REVATI, TRUE_SHEORAN, ALDEBARAN_15TAU, HIPPARCHOS, SASSANIAN, VALENS_MOON
-   **Babylonian:** BABYL_KUGLER1, BABYL_KUGLER2, BABYL_KUGLER3, BABYL_HUBER, BABYL_ETPSC, BABYL_BRITTON
-   **Epoch-based:** J2000, J1900, B1950
-   **Custom:** USER (requires `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` on the subject)

Example (Sidereal):

```json
{
    "subject": {
        "name": "John Doe",
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4826,
        "timezone": "Europe/London",
        "zodiac_type": "Sidereal",
        "sidereal_mode": "FAGAN_BRADLEY"
    }
}
```

### Custom ayanamsa (USER mode)

When using `sidereal_mode: "USER"`, you must also provide two custom ayanamsa parameters on the subject:

- `custom_ayanamsa_t0`: Julian Day number for the reference epoch (e.g., `2451545.0` for J2000.0)
- `custom_ayanamsa_ayan_t0`: Ayanamsa offset in degrees at the reference epoch (e.g., `23.5`)

Both fields are required when `sidereal_mode` is `"USER"` and are ignored for all other modes.

```json
{
    "subject": {
        "name": "Custom Sidereal",
        "year": 1990,
        "month": 6,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome",
        "zodiac_type": "Sidereal",
        "sidereal_mode": "USER",
        "custom_ayanamsa_t0": 2451545.0,
        "custom_ayanamsa_ayan_t0": 23.5
    }
}
```

## Fixed stars

The API supports 23 fixed stars as active points. Include them in the `active_points` array to add them to chart calculations and rendering:

**Original (v5.10):** Regulus, Spica

**New in v5.12:** Sirius, Canopus, Arcturus, Vega, Capella, Rigel, Procyon, Betelgeuse, Altair, Aldebaran, Antares, Pollux, Fomalhaut, Deneb, Algol, Achernar, Alcyone, Alphecca, Algorab, Deneb_Algedi, Alkaid

```json
{
    "subject": { /* ... */ },
    "active_points": ["Sun", "Moon", "Ascendant", "Sirius", "Vega", "Spica", "Regulus", "Aldebaran"]
}
```

Fixed stars include `magnitude` (visual magnitude) and `speed` (always 0.0) in the response.

## Response fields

All data endpoints return enriched point data with these fields (added in the kerykeion v5.12 engine):

| Field | Type | Description |
|-------|------|-------------|
| `speed` | `float` | Daily speed in degrees (planets, house cusps) |
| `declination` | `float` | Ecliptic declination in degrees |
| `magnitude` | `float \| null` | Visual magnitude (fixed stars only, `null` for planets) |
| `ayanamsa_value` | `float \| null` | Ayanamsa offset in degrees (sidereal charts only, `null` for tropical) |

House cusp speeds are now computed via Swiss Ephemeris `houses_ex2()` instead of returning `null` or `360.0`.

These fields are always present in the response — no request parameters needed.

## House systems

Select the house system via subject.houses_system_identifier using one of the codes:

-   A: Equal
-   B: Alcabitius
-   C: Campanus
-   D: Equal (MC)
-   F: Carter poli-equ.
-   H: Horizon/Azimut
-   I: Sunshine
-   i: Sunshine/Alt.
-   K: Koch
-   L: Pullen SD
-   M: Morinus
-   N: Equal/1=Aries
-   O: Porphyry
-   P: Placidus (common default)
-   Q: Pullen SR
-   R: Regiomontanus
-   S: Sripati
-   T: Polich/Page (Koch/Topocentric variant)
-   U: Krusinski-Pisa-Goelzer
-   V: Equal/Vehlow
-   W: Equal/Whole Sign
-   X: Axial rotation/Meridian houses
-   Y: APC houses

Example:

```json
{
    "subject": {
        "name": "John Doe",
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4826,
        "timezone": "Europe/London",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P"
    }
}
```

## Automatic coordinates (optional)

Astrologer-API can automatically resolve **latitude**, **longitude**, and **timezone** from a city name using GeoNames.
When `geonames_username` is present in `subject`, explicit `latitude` / `longitude` / `timezone` fields are not required and the API will look them up for you.

1. **Create a free GeoNames account**  
   Sign up for a free username here:  
   <a href="https://www.geonames.org/login" target="_blank" rel="noopener noreferrer">https://www.geonames.org/login</a>

2. **Send `city`, `nation`, and your `geonames_username`**  
   - `city`: full city name, including state/region if helpful  
     - e.g. `"city": "Jamaica, New York"`  
   - `nation`: 2-letter ISO country code (e.g. `"US"`, `"GB"`, `"IT"`)  
   - `geonames_username`: the username you registered on GeoNames

Example request:

```json
{
	"subject": {
		"city": "Jamaica, New York",
		"nation": "US",
		"year": 1980,
		"month": 12,
		"day": 12,
		"hour": 12,
		"minute": 12,
		"geonames_username": "YOUR_GEONAMES_USERNAME"
	}
}
```

Tip: For best accuracy, send actual coordinates when you can. GeoNames is free up to ~10k requests/day; beyond that, consider caching or using explicit `latitude` / `longitude` / `timezone`.

## Troubleshooting

### Strict Input Validation

The API enforces strict input validation and **does not allow extra fields** in requests. If you send a field that doesn't exist in the schema, you'll receive a 422 error with a helpful suggestion.

### Common Field Name Mistakes

| ❌ Wrong              | ✅ Correct                 | Notes                                                               |
| --------------------- | -------------------------- | ------------------------------------------------------------------- |
| `country`             | `nation`                   | Use 2-letter ISO 3166-1 alpha-2 code (e.g., "US", "GB")             |
| `state`               | Include in `city`          | Write `"city": "Amherst, Massachusetts"` instead of separate fields |
| `house_system`        | `houses_system_identifier` | Use single-letter identifier (e.g., "P" for Placidus)               |
| `lat` / `lng` / `lon` | `latitude` / `longitude`   | Use full field names                                                |
| `tz`                  | `timezone`                 | Use IANA timezone (e.g., "America/New_York")                        |

### City and State Format

**Important:** The `state` field does not exist. Include the state or region in the `city` field:

```json
{
    "city": "Amherst, Massachusetts",
    "nation": "US"
}
```

This also applies to other administrative divisions:

-   `"city": "Milan, Lombardy"` or just `"city": "Milan"`
-   `"city": "Paris, Île-de-France"` or just `"city": "Paris"`

### Other Common Issues

-   **422 Unprocessable Entity**: Double‑check required fields (subject.year/month/day/hour/minute and location). `/chart-data/*` endpoints reject rendering options such as theme, language, split_chart, transparent_background, show_house_position_comparison, show_cusp_position_comparison, show_degree_indicators, show_aspect_icons, custom_title.
-   **Timezone errors**: Use a valid tz database name (e.g. "Europe/Rome").
-   **Empty SVG or missing wheel/grid**: Use `/chart/*` endpoints for rendering. `/chart-data/*` never return SVG.

## Integration Guide

Since the API returns raw SVG strings, you can easily embed them in any web application.

### 1. Pure HTML/Javascript

```html
<div id="chart-container"></div>

<script>
    // Assume 'data' is the JSON response from the API
    const chartSvg = data.chart;
    document.getElementById('chart-container').innerHTML = chartSvg;
</script>
```

### 2. React (Next.js / CRA)

Use `dangerouslySetInnerHTML` to render the SVG string.

```jsx
function AstrologyChart({ svgString }) {
    return (
        <div
            className="chart-wrapper"
            dangerouslySetInnerHTML={{ __html: svgString }}
        />
    );
}
```

### 3. Vue.js (Nuxt / Vite)

Use the `v-html` directive.

```vue
<template>
    <div class="chart-wrapper" v-html="svgString"></div>
</template>

<script setup>
defineProps(['svgString']);
</script>
```

### Styling

The SVGs are responsive by default. You can control their size via the container:

```css
.chart-wrapper svg {
    width: 100%;
    height: auto;
    max-width: 600px;
}
```

## Subscription and support

Subscribe: <a href="https://rapidapi.com/gbattaglia/api/astrologer/pricing" target="_blank">https://rapidapi.com/gbattaglia/api/astrologer/pricing</a>

If you need higher quotas or a custom plan beyond the default tiers, reach out via [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com) to discuss tailored options.

Licensing note: Astrologer API is open source (AGPLv3). Using the hosted API via RapidAPI is allowed in any app, including closed‑source since is a third-party service.

<a href="https://github.com/g-battaglia/Astrologer-API" target="_blank">Astrologer-API Source Code</a>
