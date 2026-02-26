---
title: 'Now Chart'
description: 'View the current global sky with the "Now" Chart endpoint. Instant SVG rendering of real-time planetary positions for universal reference.'
order: 2
---

# Now Chart Endpoint

## `POST /api/v5/now/chart`

> **📘 [View Complete Example](../examples/now_chart_svg.md)**

This endpoint generates a **real-time astrological chart** for the current moment in UTC (Universal Time Coordinated). It automatically captures the current positions of all celestial bodies and renders them as a visual SVG chart wheel.

Unlike a natal chart which is fixed to a birth date, the "Now" chart is dynamic and represents the current astrological "weather" or cosmic climate. The chart is calculated for the Prime Meridian (Greenwich, UK) to provide a universal reference point.

**Use cases:**

-   **Daily Horoscope Features**: Display the current planetary alignments
-   **Astrological Weather Apps**: Show real-time cosmic conditions
-   **Electional Astrology**: Determine the best timing for events
-   **Teaching Tools**: Demonstrate how planetary positions change over time
-   **Live Event Charts**: Capture the astrological signature of moment-specific events

This endpoint is perfect for applications that need to display the "cosmic now" without requiring users to input any birth data.

### Request Body

-   **`name`** (string, optional): Custom name for the chart title (default: "Now").
-   **`zodiac_type`**, **`sidereal_mode`**, **`houses_system_identifier`** (optional configuration).
-   **`theme`**, **`language`**, **`split_chart`**, `transparent_background`, `show_house_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title` (rendering options).

#### Complete Request Example

```json
{
    "name": "Current Sky",
    "theme": "light",
    "language": "IT",
    "houses_system_identifier": "W"
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): Calculated data for now.
-   **`chart`** (string): SVG string.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
