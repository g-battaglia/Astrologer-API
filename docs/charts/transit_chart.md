---
title: 'Transit Chart'
description: 'Monitor the "cosmic weather" with SVG transit charts. Compare current planetary positions against a natal foundation for precise predictive visualization.'
order: 5
---

# Transit Chart Endpoint

## `POST /api/v5/chart/transit`

> **[View Complete Example](../examples/transit_chart_svg)**

This endpoint generates a **transit chart** as a dual-wheel SVG visualization, showing how current (or future) planetary positions interact with a person's natal chart. Transits are the foundation of predictive astrology, revealing timing for opportunities, challenges, and significant life events.

### Chart Preview

![Transit Chart Example](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_transit.svg)

The chart displays:

-   **Inner Wheel**: The natal (birth) chart — the permanent foundation
-   **Outer Wheel**: The transit chart — current or future planetary positions
-   **Transit-to-Natal Aspects**: How transiting planets aspect natal planets and points

**Use cases:**

-   **Personal Forecasting**: Predict important periods for career, relationships, health
-   **Timing Decisions**: Choose optimal moments for major life changes
-   **Understanding Current Events**: Gain perspective on why certain themes are emerging
-   **Yearly Planning**: Map out the astrological landscape for the year ahead

### Request Body

-   **`first_subject`** (object, required): Natal subject. See [Subject Object Reference](../README.md#subject-object-reference).
    ```json
    {
        "name": "Natal Subject",
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
-   **`transit_subject`** (object, required): Transit moment. Uses a simplified subject model — does **not** include `zodiac_type`, `sidereal_mode`, `perspective_type`, or `houses_system_identifier` (these are inherited from `first_subject`). The `name` field defaults to `"Transit"`.
    ```json
    {
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
    ```

**Transit-specific options** (optional):

-   **`include_house_comparison`** (boolean): Include house overlay comparison in the data. Default: `true`.

**Computation options** (optional):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

**Rendering options** (optional):

-   **`theme`** (string): Visual theme. Default: `"classic"`. See [Themes](../README.md#themes).
-   **`language`** (string): Language for chart labels. Default: `"EN"`. See [Languages](../README.md#languages).
-   **`style`** (string): `"classic"` (default) or `"modern"`.
-   **`split_chart`** (boolean): Return separate `chart_wheel` and `chart_grid` SVGs. Default: `false`.
-   **`transparent_background`** (boolean): Render with transparent background. Default: `false`.
-   **`custom_title`** (string): Override the chart title (max 40 characters).
-   **`show_house_position_comparison`** (boolean): Show the house comparison table. Default: `true`.
-   **`show_cusp_position_comparison`** (boolean): Show cusp comparison grids for natal vs transit. Default: `true`.
-   **`show_degree_indicators`** (boolean): Show radial lines and degree numbers. Default: `true`.
-   **`show_aspect_icons`** (boolean): Show aspect icons on aspect lines. Default: `true`.
-   **`show_zodiac_background_ring`** (boolean): Show colored zodiac wedges (`"modern"` style only). Default: `true`.
-   **`double_chart_aspect_grid_type`** (string): Aspect display layout — `"list"` (default) or `"table"`.

#### Complete Request Example

```json
{
    "first_subject": {
        "name": "Natal Subject",
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
    "transit_subject": {
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    },
    "theme": "classic",
    "style": "modern",
    "show_zodiac_background_ring": true,
    "double_chart_aspect_grid_type": "list"
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): Transit data (same structure as the [Transit Chart Data](../data/chart_data_transit.md) endpoint).
-   **`chart`** (string): SVG string (when `split_chart` is `false`).
-   **`chart_wheel`** (string): SVG of the dual wheel (when `split_chart` is `true`).
-   **`chart_grid`** (string): SVG of the aspect grid (when `split_chart` is `true`).

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
