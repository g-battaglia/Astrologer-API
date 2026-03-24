---
title: 'Now Chart'
description: 'View the current global sky with the "Now" Chart endpoint. Instant SVG rendering of real-time planetary positions for universal reference.'
order: 2
---

# Now Chart Endpoint

## `POST /api/v5/now/chart`

> **[View Complete Example](../examples/now_chart_svg)**

This endpoint generates a **real-time astrological chart** for the current moment in UTC (Universal Time Coordinated). It automatically captures the current positions of all celestial bodies and renders them as a visual SVG chart wheel.

### Chart Preview

![Now Chart Example](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/now_chart.svg)

Unlike a natal chart which is fixed to a birth date, the \"Now\" chart is dynamic and represents the current astrological \"weather\" or cosmic climate. The chart is calculated for the Prime Meridian (Greenwich, UK) to provide a universal reference point.

**Use cases:**

-   **Daily Horoscope Features**: Display the current planetary alignments
-   **Astrological Weather Apps**: Show real-time cosmic conditions
-   **Electional Astrology**: Determine the best timing for events
-   **Teaching Tools**: Demonstrate how planetary positions change over time
-   **Live Event Charts**: Capture the astrological signature of moment-specific events

This endpoint does **not** require a `subject` object — configuration fields are provided at the request body root level.

### Request Body

**Configuration options** (optional):

-   **`name`** (string): Custom name for the chart title. Default: `"Now"`.
-   **`zodiac_type`** (string): `"Tropical"` (default) or `"Sidereal"`.
-   **`sidereal_mode`** (string): Ayanamsa system. Required when `zodiac_type` is `"Sidereal"`. See [Sidereal Modes](../README.md#sidereal-modes).
-   **`perspective_type`** (string): Astronomical perspective. Default: `"Apparent Geocentric"`. See [Perspective Types](../README.md#perspective-types).
-   **`houses_system_identifier`** (string): House system code. Default: `"P"` (Placidus). See [House Systems](../README.md#house-systems).

**Computation options** (optional):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

**Rendering options** (optional):

-   **`theme`** (string): Visual theme — `"classic"` (default), `"light"`, `"dark"`, `"dark-high-contrast"`, `"strawberry"`, `"black-and-white"`. See [Themes](../README.md#themes).
-   **`language`** (string): Language for chart labels. Default: `"EN"`. See [Languages](../README.md#languages).
-   **`style`** (string): `"classic"` (default) or `"modern"`.
-   **`split_chart`** (boolean): Return separate `chart_wheel` and `chart_grid` SVGs. Default: `false`.
-   **`transparent_background`** (boolean): Render with transparent background. Default: `false`.
-   **`custom_title`** (string): Override the chart title (max 40 characters).
-   **`show_house_position_comparison`** (boolean): Show the house/points comparison table. Default: `true`.
-   **`show_degree_indicators`** (boolean): Show radial lines and degree numbers. Default: `true`.
-   **`show_aspect_icons`** (boolean): Show aspect icons on aspect lines. Default: `true`.
-   **`show_zodiac_background_ring`** (boolean): Show colored zodiac wedges (`"modern"` style only). Default: `true`.

#### Complete Request Example

```json
{
    "name": "Current Sky",
    "theme": "light",
    "language": "IT",
    "style": "modern",
    "show_zodiac_background_ring": true,
    "houses_system_identifier": "W"
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): Calculated chart data for the current moment.
-   **`chart`** (string): SVG string (when `split_chart` is `false`).
-   **`chart_wheel`** (string): SVG of the wheel only (when `split_chart` is `true`).
-   **`chart_grid`** (string): SVG of the aspect grid only (when `split_chart` is `true`).

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
