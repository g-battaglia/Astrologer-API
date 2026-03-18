---
title: 'Natal Chart Context'
description: 'Get structured astrological data and summaries to provide context for AI-driven birth chart interpretations. Optimized for Large Language Models (LLMs).'
order: 3
---

# Natal Chart Context Endpoint

## `POST /api/v5/context/birth-chart`

> **📘 [View Complete Example](../examples/natal_context.md)**

Generates an AI-powered interpretation of a full natal chart. Unlike the simple subject context, this endpoint analyzes the complete chart data, including house systems and aspects, providing a deeper and more comprehensive reading of the birth chart's dynamics.

### Request Body

-   **`subject`** (object, required): The subject's birth data (same structure as `/api/v5/chart-data/birth-chart`).
    ```json
    {
        "name": "Subject Name",
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
-   **Computation options**: `active_points`, `active_aspects`, `distribution_method`, `custom_distribution_weights` (identical to the natal chart-data endpoint). Rendering options such as `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title` are **not** accepted here.

#### Complete Request Example

```json
{
    "subject": {
        "name": "Subject Name",
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
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`context`** (string): The generated AI XML context string for the natal chart.
-   **`chart_data`** (object): The complete calculated chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Natal\"><subject>Subject Name</subject>...</chart_analysis>",
  "chart_data": {
    "subject": { ... },
    "houses_list": [ ... ],
    "aspects_list": [ ... ]
    // ... full chart data
  }
}
```
