---
title: 'Lunar Return Chart'
description: 'Track monthly emotional cycles with SVG Lunar Return charts. High-precision rendering of the Moon''s monthly return for short-term forecasting.'
order: 7
---

# Lunar Return Chart Endpoint

## `POST /api/v5/chart/lunar-return`

> **[View Complete Example](../examples/lunar_return_chart_svg)**

This endpoint generates a **Lunar Return chart**, a monthly predictive chart that occurs when the transiting Moon returns to the exact position of your natal Moon (approximately every 27.3 days). While less commonly known than Solar Returns, Lunar Returns are powerful tools for understanding monthly emotional rhythms and short-term forecasting.

### Chart Preview

![Lunar Return Chart Example](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_lunar_return.svg)

The Lunar Return chart is valid for approximately one month and reveals:

-   Emotional themes and inner experiences
-   Domestic and family matters
-   Health and daily routines
-   Short-term opportunities and challenges

**Chart Options**:

-   **Dual Wheel** (default): Shows natal chart (inner) and lunar return (outer)
-   **Single Wheel**: Shows only the lunar return chart

**Key Differences from Solar Returns**:

-   **Frequency**: Monthly instead of yearly
-   **Focus**: Emotional/domestic vs. major life themes
-   **Duration**: ~27 days vs. 1 year

**Use cases:**

-   **Monthly Planning**: Understand the emotional tone of each lunar cycle
-   **Timing Short-term Events**: Choose optimal dates within the month
-   **Emotional Forecasting**: Anticipate mood shifts and inner needs
-   **Complementing Solar Returns**: Add monthly detail to yearly forecasts

### Request Body

-   **`subject`** (object, required): Natal subject. See [Subject Object Reference](../README.md#subject-object-reference).
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

**Search parameters** (provide `year` or `iso_datetime`):

-   **`year`** (integer, required unless `iso_datetime` is set): Calendar year to search for the next return (1-3000).
-   **`month`** (integer, optional): Month (1-12) to start the search from. Requires `year`.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to `1`. Useful for finding the second Lunar Return in a month.
-   **`iso_datetime`** (string, optional): ISO 8601 formatted datetime to start the search from. E.g. `"2025-05-01T00:00:00+00:00"`. Alternative to `year`/`month`/`day`.

**Return-specific options** (optional):

-   **`wheel_type`** (string): `"dual"` (default) or `"single"`. Single wheel shows only the return chart.
-   **`include_house_comparison`** (boolean): Include house overlay comparison for dual wheel. Default: `true`. Automatically set to `false` when `wheel_type` is `"single"`.
-   **`return_location`** (object, optional): Override the location for the return chart. If omitted, the natal subject's location is used.

    | Field | Type | Description |
    |-------|------|-------------|
    | `city` | string | Target city name. Falls back to natal city if omitted. |
    | `nation` | string | Two-letter ISO country code. Falls back to natal nation if omitted. |
    | `longitude` | float | Longitude (-180 to 180). |
    | `latitude` | float | Latitude (-90 to 90). |
    | `timezone` | string | IANA timezone identifier. |
    | `altitude` | float | Altitude in meters. |
    | `geonames_username` | string | GeoNames username to resolve location from city/nation. |

    Provide all three of `latitude`, `longitude`, and `timezone` for offline mode, or use `geonames_username` for online resolution.

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
-   **`show_cusp_position_comparison`** (boolean): Show cusp comparison table (dual wheel only). Default: `true`.
-   **`show_degree_indicators`** (boolean): Show radial lines and degree numbers. Default: `true`.
-   **`show_aspect_icons`** (boolean): Show aspect icons on aspect lines. Default: `true`.
-   **`show_zodiac_background_ring`** (boolean): Show colored zodiac wedges (`"modern"` style only). Default: `true`.
-   **`double_chart_aspect_grid_type`** (string): Aspect display layout — `"list"` (default) or `"table"`.

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
    "wheel_type": "dual",
    "theme": "light",
    "style": "modern",
    "show_zodiac_background_ring": true
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`return_type`** (string): `"Lunar"`.
-   **`wheel_type`** (string): `"dual"` or `"single"`.
-   **`chart_data`** (object): Return chart data (same structure as the [Lunar Return Data](../data/chart_data_lunar_return.md) endpoint).
-   **`chart`** (string): SVG string (when `split_chart` is `false`).
-   **`chart_wheel`** (string): SVG of the wheel (when `split_chart` is `true`).
-   **`chart_grid`** (string): SVG of the aspect grid (when `split_chart` is `true`).

#### Complete Response Example

```json
{
  "status": "OK",
  "return_type": "Lunar",
  "wheel_type": "dual",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
