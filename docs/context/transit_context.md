---
title: 'Transit Context'
description: 'Get structured planetary transit data and summaries for AI-driven predictive astrology. Provides the essential context for LLMs to interpret current life themes.'
order: 6
---

# Transit Context Endpoint

## `POST /api/v5/context/transit`

> **📘 [View Complete Example](../examples/transit_context.md)**

Generates an AI-powered interpretation of a transit chart. This endpoint analyzes how the current (or future) positions of the planets affect a person's natal chart. It is essential for forecasting, understanding current life themes, and predictive astrology.

### Request Body

-   **`first_subject`** (object, required): The Natal Subject (the person receiving the transits).
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
-   **`transit_subject`** (object, required): The Transit Moment (the time and place of the event/now).
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
-   **Computation options**: flags such as `include_house_comparison`, `active_points`, `active_aspects`, `distribution_method`, `custom_distribution_weights` (identical to `/api/v5/chart-data/transit`). Rendering options like `theme`, `language`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `custom_title` are **not** accepted here.

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
    }
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`context`** (string): The generated AI text interpretation of the transits.
-   **`chart_data`** (object): The complete calculated transit chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "Transit Analysis for Natal Subject...\nTransiting Jupiter is conjunct Natal Sun...",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... }, // Transit subject
    "aspects_list": [ ... ]
    // ... full transit data
  }
}
```
