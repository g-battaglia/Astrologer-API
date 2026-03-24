---
title: 'Composite Context'
description: 'Get formatted composite chart data and relationship summaries for AI interpretation. Provides the relational context for LLMs to generate partnership insights.'
order: 5
---

# Composite Context Endpoint

## `POST /api/v5/context/composite`

> **[View Complete Example](../examples/composite_context)**

Generates an AI-optimized XML-structured interpretation of a composite chart. A composite chart is a single chart calculated from the midpoints of two people's charts, representing the relationship itself as a third entity. This endpoint provides insights into the purpose, destiny, and core nature of the partnership.

### Request Body

-   **`first_subject`** (object, required): First partner. See [Subject Object Reference](../README.md#subject-object-reference).
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
-   **`second_subject`** (object, required): Second partner. Same structure as `first_subject`.
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

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

Rendering options (`theme`, `language`, `style`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `custom_title`) are **not** accepted on this endpoint.

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

-   **`status`** (string): `"OK"`.
-   **`context`** (string): The AI-optimized XML context string for the composite chart.
-   **`chart_data`** (object): The complete calculated composite chart data (same structure as the [Composite Chart Data](../data/chart_data_composite.md) endpoint).

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Composite\"><subject>Composite</subject>...</chart_analysis>",
  "chart_data": {
    "subject": { ... },
    "aspects": [ ... ],
    "elements_distribution": { ... },
    "qualities_distribution": { ... }
  }
}
```
