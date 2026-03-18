---
title: 'Synastry Context'
description: 'Retrieve formatted synastry data and relationship summaries to serve as context for AI interpretation. Optimized for relationship compatibility analysis using LLMs.'
order: 4
---

# Synastry Context Endpoint

## `POST /api/v5/context/synastry`

> **📘 [View Complete Example](../examples/synastry_context.md)**

Generates an AI-powered interpretation of a synastry (relationship) chart. This endpoint analyzes the astrological compatibility and dynamics between two subjects, providing insights into their relationship strengths, challenges, and overall chemistry.

### Request Body

-   **`first_subject`** (object, required): The first partner (Inner Wheel).
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
-   **`second_subject`** (object, required): The second partner (Outer Wheel).
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
-   **Computation options**: flags such as `include_house_comparison`, `include_relationship_score`, `active_points`, `active_aspects`, `distribution_method`, `custom_distribution_weights` (identical to `/api/v5/chart-data/synastry`). Rendering options like `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title` are **not** accepted here.

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
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
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
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    }
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`context`** (string): The generated AI XML context string for the relationship.
-   **`chart_data`** (object): The complete calculated synastry chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Synastry\"><first_subject>Partner A</first_subject><second_subject>Partner B</second_subject>...</chart_analysis>",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... },
    "aspects_list": [ ... ]
    // ... full synastry data
  }
}
```
