---
title: 'Natal Chart'
description: 'Generate professional SVG natal charts with the Birth Chart endpoint. Customizable themes, language support, and machine-readable astrological data.'
order: 1
---

# Natal Chart Endpoint

## `POST /api/v5/chart/birth-chart`

> **[View Complete Example](../examples/natal_chart_svg)**

This endpoint generates a **visual birth chart** (natal chart) as an SVG image, along with the complete calculated astrological data. A birth chart is a snapshot of the sky at the exact moment and location of a person's birth, showing the positions of planets, houses, and astrological points.

### Chart Preview

![Natal Chart Example](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_natal.svg)

The returned SVG is a professional-quality chart wheel that can be:

-   Embedded directly in web pages or mobile apps
-   Downloaded and printed
-   Customized with themes (classic, dark, dark-high-contrast, light, strawberry, black-and-white)
-   Split into separate wheel and aspect grid components

**Use cases:**

-   Generating personalized birth charts for users
-   Creating printable chart reports
-   Building astrology reading applications
-   Visualizing natal placements for interpretation

### Request Body

-   **`subject`** (object, required): The subject's birth data. See [Subject Object Reference](../README.md#subject-object-reference) for all fields.
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

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. E.g. `[{"name": "conjunction", "orb": 10}]`. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

**Rendering options** (optional):

-   **`theme`** (string): Visual theme — `"classic"` (default), `"light"`, `"dark"`, `"dark-high-contrast"`, `"strawberry"`, `"black-and-white"`. See [Themes](../README.md#themes).
-   **`language`** (string): Language for chart labels — `"EN"` (default), `"FR"`, `"PT"`, `"IT"`, `"CN"`, `"ES"`, `"RU"`, `"TR"`, `"DE"`, `"HI"`. See [Languages](../README.md#languages).
-   **`style`** (string): `"classic"` (default, traditional wheel) or `"modern"` (concentric rings).
-   **`split_chart`** (boolean): If `true`, returns separate `chart_wheel` and `chart_grid` SVGs instead of a single `chart`. Default: `false`.
-   **`transparent_background`** (boolean): Render with transparent background. Default: `false`.
-   **`custom_title`** (string): Override the chart title (max 40 characters).
-   **`show_house_position_comparison`** (boolean): Show the house/points comparison table. Default: `true`.
-   **`show_degree_indicators`** (boolean): Show radial lines and degree numbers for planet positions. Default: `true`.
-   **`show_aspect_icons`** (boolean): Show aspect icons on aspect lines. Default: `true`.
-   **`show_zodiac_background_ring`** (boolean): Show colored zodiac wedges (only affects `"modern"` style). Default: `true`.

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
    "style": "modern",
    "show_zodiac_background_ring": true,
    "split_chart": false,
    "transparent_background": true
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The calculated chart data (same structure as the [Natal Chart Data](../data/chart_data_natal.md) endpoint).
-   **`chart`** (string): The full SVG string (when `split_chart` is `false`).
-   **`chart_wheel`** (string): SVG of the wheel only (when `split_chart` is `true`).
-   **`chart_grid`** (string): SVG of the aspect grid only (when `split_chart` is `true`).

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg xmlns='http://www.w3.org/2000/svg' ...> ... </svg>"
}
```
