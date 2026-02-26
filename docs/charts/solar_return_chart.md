---
title: 'Solar Return Chart'
description: 'Map out the solar year with SVG Solar Return charts. Professional dual-wheel and relocation support for accurate annual birthday forecasting.'
order: 6
---

# Solar Return Chart Endpoint

## `POST /api/v5/chart/solar-return`

> **📘 [View Complete Example](../examples/solar_return_chart_svg.md)**

This endpoint generates a **Solar Return chart**, one of the most important timing techniques in predictive astrology. A Solar Return occurs annually when the transiting Sun returns to the exact degree, minute, and second of your natal Sun position - essentially, it's your true "astrological birthday."

The Solar Return chart is valid for one full year (from one birthday to the next) and outlines the major themes, opportunities, and challenges you'll encounter during that solar year.

**Chart Options**:

-   **Dual Wheel** (default): Shows natal chart (inner) and solar return (outer) for comparison
-   **Single Wheel**: Shows only the solar return chart

**Relocation Feature**:
The chart can be calculated for different locations, which is significant because:

-   The chart is cast for the exact moment the Sun returns
-   The location determines the Ascendant and house cusps
-   Many astrologers relocate for their birthday to improve their Solar Return chart

**Use cases:**

-   **Annual Forecasting**: Preview the year ahead from birthday to birthday
-   **Birthday Planning**: Choose where to spend your birthday for optimal chart positioning
-   **Life Planning**: Understand which life areas will be emphasized this year
-   **Professional Consultations**: Essential for any predictive astrology reading
-   **Personal Review**: Reflect on patterns and themes as each solar year unfolds

**Key Points to Analyze**:

-   The Solar Return Ascendant and its ruler
-   Planets in angular houses (1st, 4th, 7th, 10th) - these dominate the year
-   Aspects between Solar Return planets and natal planets
-   The house position of the Solar Return Sun

This chart type is foundational for yearly planning and is widely used by professional astrologers worldwide.

### Request Body

-   **`subject`** (object, required): Natal subject.
    ```json
    {
        "name": "John Doe",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
    ```
-   **`year`** (integer, required): Return year.
-   **`month`** (integer, optional): Month (1-12) to start the search from.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to 1. Useful for finding later returns in the same month.
-   **`return_location`** (object, optional): Relocation.
-   **`wheel_type`** (string, optional): "dual" (default) or "single".
-   **`theme`**, **`language`**, **`split_chart`** (rendering options).
-   **`show_house_position_comparison`** (bool, optional): Show or hide the house/points comparison table (default: true).
-   **`show_cusp_position_comparison`** (bool, optional): Show or hide the cusp comparison table for dual charts (default: true).
-   **`show_degree_indicators`** (bool, optional): Display radial lines and degree numbers for planet positions on the wheel (default: true).
-   **`show_aspect_icons`** (bool, optional): Display aspect icons on aspect lines (default: true).

#### Complete Request Example

```json
{
    "subject": {
        "name": "John Doe",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London"
    },
    "year": 2024,
    "month": 10,
    "day": 1,
    "wheel_type": "dual",
    "theme": "dark"
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): Return data.
-   **`chart`** (string): SVG string.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
