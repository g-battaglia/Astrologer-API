---
title: 'Transit Chart'
description: 'Monitor the "cosmic weather" with SVG transit charts. Compare current planetary positions against a natal foundation for precise predictive visualization.'
order: 5
---

# Transit Chart Endpoint

## `POST /api/v5/chart/transit`

> **📘 [View Complete Example](../examples/transit_chart_svg.md)**

This endpoint generates a **transit chart** as a dual-wheel SVG visualization, showing how current (or future) planetary positions interact with a person's natal chart. Transits are the foundation of predictive astrology, revealing timing for opportunities, challenges, and significant life events.

The chart displays:

-   **Inner Wheel**: The natal (birth) chart - the permanent foundation
-   **Outer Wheel**: The transit chart - current or future planetary positions
-   **Transit-to-Natal Aspects**: How transiting planets aspect natal planets and points

**Key Concept**:
Transits act like "cosmic weather" passing over your natal chart. A transiting planet activates specific areas of your life and natal potentials when it forms aspects to your natal planets.

**Use cases:**

-   **Personal Forecasting**: Predict important periods for career, relationships, health
-   **Timing Decisions**: Choose optimal moments for major life changes
-   **Understanding Current Events**: Gain perspective on why certain themes are emerging
-   **Yearly Planning**: Map out the astrological landscape for the year ahead
-   **Crisis Counseling**: Understand the astrological context of challenging periods

**Common Transit Queries**:

-   Saturn Return (ages ~29 and ~58): Major life restructuring
-   Jupiter transits: Growth opportunities and expansion periods
-   Outer planet transits (Uranus, Neptune, Pluto): Deep transformation cycles

This is one of the most practically useful chart types, essential for anyone serious about timing and forecasting in astrology.

### Request Body

-   **`first_subject`** (object, required): Natal subject.
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
-   **`transit_subject`** (object, required): Transit moment.
    ```json
    {
        "name": "Transit Moment",
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London"
    }
    ```
-   **`theme`**, **`language`**, **`split_chart`** (rendering options).
-   **`show_house_position_comparison`** (bool, optional): Display the house comparison table for natal vs transit (default: true).
-   **`show_cusp_position_comparison`** (bool, optional): Display cusp comparison grids for natal vs transit houses (default: true).
-   **`show_degree_indicators`** (bool, optional): Display radial lines and degree numbers for planet positions on the wheels (default: true).
-   **`show_aspect_icons`** (bool, optional): Display aspect icons on aspect lines (default: true).

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
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London"
    },
    "transit_subject": {
        "name": "Transit Moment",
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London"
    },
    "theme": "classic"
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): Transit data.
-   **`chart`** (string): SVG string.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
