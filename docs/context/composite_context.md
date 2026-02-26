---
title: 'Composite Context'
description: 'Get formatted composite chart data and relationship summaries for AI interpretation. Provides the relational context for LLMs to generate partnership insights.'
order: 5
---

# Composite Context Endpoint

## `POST /api/v5/context/composite`

> **📘 [View Complete Example](../examples/composite_context.md)**

Generates an AI-powered interpretation of a composite chart. A composite chart is a single chart calculated from the midpoints of two people's charts, representing the relationship itself as a third entity. This endpoint provides insights into the purpose, destiny, and core nature of the partnership.

### Request Body

-   **`first_subject`** (object, required): First partner.
    ```json
    {
        "name": "Partner A",
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
-   **`second_subject`** (object, required): Second partner.
    ```json
    {
        "name": "Partner B",
        "year": 1992,
        "month": 5,
        "day": 15,
        "hour": 18,
        "minute": 30,
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    }
    ```
-   **Computation options**: `active_points`, `active_aspects`, `distribution_method`, `custom_distribution_weights` (identical to `/api/v5/chart-data/composite`). Rendering options such as `theme`, `language`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `custom_title` are **not** accepted here.

#### Complete Request Example

```json
{
    "first_subject": {
        "name": "Partner A",
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
    "second_subject": {
        "name": "Partner B",
        "year": 1992,
        "month": 5,
        "day": 15,
        "hour": 18,
        "minute": 30,
        "city": "New York",
        "nation": "US",
        "lng": -74.006,
        "lat": 40.7128,
        "tz_str": "America/New_York"
    }
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`context`** (string): The generated AI text interpretation of the composite chart.
-   **`chart_data`** (object): The complete calculated composite chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "Composite Chart Analysis...\nThe relationship has a Sun in the 7th House...",
  "chart_data": {
    "subject": { ... }, // Composite subject
    "aspects_list": [ ... ]
    // ... full composite data
  }
}
```
