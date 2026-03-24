---
title: 'Natal Chart Context'
description: 'Get structured astrological data and summaries to provide context for AI-driven birth chart interpretations. Optimized for Large Language Models (LLMs).'
order: 3
---

# Natal Chart Context Endpoint

## `POST /api/v5/context/birth-chart`

> **[View Complete Example](../examples/natal_context)**

Generates an AI-optimized XML-structured interpretation of a full natal chart. Unlike the simple subject context, this endpoint analyzes the complete chart data, including house systems, aspects, and element/quality distributions, providing a deeper and more comprehensive reading of the birth chart's dynamics.

### Request Body

-   **`subject`** (object, required): The subject's birth data. See [Subject Object Reference](../README.md#subject-object-reference).
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

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

Rendering options (`theme`, `language`, `style`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`) are **not** accepted on this endpoint.

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

-   **`status`** (string): `"OK"`.
-   **`context`** (string): The AI-optimized XML context string for the natal chart.
-   **`chart_data`** (object): The complete calculated chart data (same structure as the [Natal Chart Data](../data/chart_data_natal.md) endpoint).

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Natal\"><subject>Subject Name</subject>...</chart_analysis>",
  "chart_data": {
    "subject": { ... },
    "aspects": [ ... ],
    "elements_distribution": { ... },
    "qualities_distribution": { ... }
  }
}
```
