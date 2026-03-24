---
title: 'Synastry Context'
description: 'Retrieve formatted synastry data and relationship summaries to serve as context for AI interpretation. Optimized for relationship compatibility analysis using LLMs.'
order: 4
---

# Synastry Context Endpoint

## `POST /api/v5/context/synastry`

> **[View Complete Example](../examples/synastry_context)**

Generates an AI-optimized XML-structured interpretation of a synastry (relationship) chart. This endpoint analyzes the astrological compatibility and dynamics between two subjects, providing insights into their relationship strengths, challenges, and overall chemistry.

### Request Body

-   **`first_subject`** (object, required): The first partner (inner wheel). See [Subject Object Reference](../README.md#subject-object-reference).
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
-   **`second_subject`** (object, required): The second partner (outer wheel). Same structure as `first_subject`.
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

**Synastry-specific options** (optional):

-   **`include_house_comparison`** (boolean): Include house overlay analysis. Default: `true`.
-   **`include_relationship_score`** (boolean): Include Ciro Discepolo compatibility score. Default: `true`.

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
-   **`context`** (string): The AI-optimized XML context string for the relationship.
-   **`chart_data`** (object): The complete calculated synastry chart data (same structure as the [Synastry Chart Data](../data/chart_data_synastry.md) endpoint).

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Synastry\"><first_subject>Partner A</first_subject><second_subject>Partner B</second_subject>...</chart_analysis>",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... },
    "aspects": [ ... ],
    "relationship_score": { ... }
  }
}
```
