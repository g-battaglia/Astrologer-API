---
title: 'Natal Chart'
description: 'Generate professional SVG natal charts with the Birth Chart endpoint. Customizable themes, language support, and machine-readable astrological data.'
order: 1
---

# Natal Chart Endpoint

## `POST /api/v5/chart/birth-chart`

> **📘 [View Complete Example](../examples/natal_chart_svg.md)**

This endpoint generates a **visual birth chart** (natal chart) as an SVG image, along with the complete calculated astrological data. A birth chart is a snapshot of the sky at the exact moment and location of a person's birth, showing the positions of planets, houses, and astrological points.

The returned SVG is a professional-quality chart wheel that can be:

-   Embedded directly in web pages or mobile apps
-   Downloaded and printed
-   Customized with themes (classic, dark, high contrast)
-   Split into separate wheel and aspect grid components

**Use cases:**

-   Generating personalized birth charts for users
-   Creating printable chart reports
-   Building astrology reading applications
-   Visualizing natal placements for interpretation

The endpoint combines the power of precise astronomical calculations with beautiful visual rendering, making it ideal for both professional astrologers and hobbyists.

### Request Body

-   **`subject`** (object, required): The subject's birth data.
    ```json
    {
        "name": "Alice",
        "year": 1995,
        "month": 6,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Berlin",
        "nation": "DE",
        "longitude": 13.405,
        "latitude": 52.52,
        "timezone": "Europe/Berlin"
    }
    ```
-   **`active_points`** (array, optional): Points to include.
-   **`active_aspects`** (array, optional): Aspects to include.
-   **`show_aspect_icons`** (boolean, optional): Display aspect icons on aspect lines (default: true).
-   **`theme`** (string, optional): Color theme for the chart (e.g., "classic", "dark", "high_contrast"). Default: "classic".
-   **`language`** (string, optional): Language for chart labels (e.g., "EN", "IT", "ES"). Default: "EN".
-   **`split_chart`** (bool, optional): If true, returns the chart wheel and aspect grid as separate SVG strings. Default: false.
-   **`transparent_background`** (bool, optional): If true, the chart background will be transparent. Default: false.
-   **`show_house_position_comparison`** (bool, optional): Show or hide the houses/points comparison table next to the wheel. Default: true.
-   **`show_degree_indicators`** (bool, optional): Show radial lines and degree numbers for planet positions on the wheel. Default: true.
-   **`custom_title`** (string, optional): Override the default chart title.

#### Complete Request Example

```json
{
    "subject": {
        "name": "Alice",
        "year": 1995,
        "month": 6,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Berlin",
        "nation": "DE",
        "longitude": 13.405,
        "latitude": 52.52,
        "timezone": "Europe/Berlin"
    },
    "theme": "dark",
    "language": "EN",
    "split_chart": false,
    "transparent_background": true
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): The calculated chart data (same as chart-data endpoint).
-   **`chart`** (string): The full SVG string of the chart (if `split_chart` is false).
-   **`chart_wheel`** (string): SVG of the wheel (if `split_chart` is true).
-   **`chart_grid`** (string): SVG of the aspect grid (if `split_chart` is true).

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg xmlns='http://www.w3.org/2000/svg' ...> ... </svg>"
}
```
