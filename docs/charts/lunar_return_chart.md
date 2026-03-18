---
title: 'Lunar Return Chart'
description: 'Track monthly emotional cycles with SVG Lunar Return charts. High-precision rendering of the Moon''s monthly return for short-term forecasting.'
order: 7
---

# Lunar Return Chart Endpoint

## `POST /api/v5/chart/lunar-return`

> **📘 [View Complete Example](../examples/lunar_return_chart_svg.md)**

This endpoint generates a **Lunar Return chart**, a monthly predictive chart that occurs when the transiting Moon returns to the exact position of your natal Moon (approximately every 27.3 days). While less commonly known than Solar Returns, Lunar Returns are powerful tools for understanding monthly emotional rhythms and short-term forecasting.

The Lunar Return chart is valid for approximately one month and reveals:

-   Emotional themes and inner experiences
-   Domestic and family matters
-   Health and daily routines
-   Short-term opportunities and challenges
-   Public reception and popularity fluctuations

**Chart Options**:

-   **Dual Wheel** (default): Shows natal chart (inner) and lunar return (outer)
-   **Single Wheel**: Shows only the lunar return chart

**Key Differences from Solar Returns**:

-   **Frequency**: Monthly instead of yearly
-   **Focus**: Emotional/domestic vs. major life themes
-   **Duration**: ~27 days vs. 1 year
-   **Interpretation**: More fluid and subtle; reflects inner states and immediate environment

**Use cases:**

-   **Monthly Planning**: Understand the emotional tone of each lunar cycle
-   **Timing Short-term Events**: Choose optimal dates within the month
-   **Emotional Forecasting**: Anticipate mood shifts and inner needs
-   **Complementing Solar Returns**: Add monthly detail to yearly forecasts
-   **Women's Health**: Particularly useful for understanding monthly cycles and fertility patterns

**Best Practices**:

-   Track several consecutive Lunar Returns to see patterns
-   Pay special attention to the Lunar Return Ascendant and Moon's house placement
-   Note which natal house is activated by the Lunar Return Ascendant
-   Consider Lunar Returns alongside transits for comprehensive timing

This chart type is especially valued by astrologers who work with clients on an ongoing basis, providing monthly check-ins and guidance.

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
-   **`year`** (integer, required): Year.
-   **`month`** (integer, optional): Month (1-12) to start the search from.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to 1. Useful for finding the second Lunar Return in a month.
-   **`wheel_type`** (string, optional): "dual" or "single".
-   **`theme`**, **`language`**, **`split_chart`** (rendering options).
-   **`style`** (string, optional): Chart wheel layout — "classic" (default) or "modern". Default: "classic".
-   **`show_zodiac_background_ring`** (bool, optional): Show colored zodiac wedges behind the wheel, modern style only. Default: true.
-   **`double_chart_aspect_grid_type`** (string, optional): Aspect display for dual charts — "list" (default) or "table". Default: "list".
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
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    },
    "year": 2024,
    "month": 5,
    "day": 1,
    "wheel_type": "single",
    "theme": "light",
    "style": "modern",
    "show_zodiac_background_ring": true,
    "double_chart_aspect_grid_type": "list"
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
