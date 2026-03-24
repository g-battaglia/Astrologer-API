---
title: 'Transit Context'
description: 'Get structured planetary transit data and summaries for AI-driven predictive astrology. Provides the essential context for LLMs to interpret current life themes.'
order: 6
---

# Transit Context Endpoint

## `POST /api/v5/context/transit`

> **[View Complete Example](../examples/transit_context)**

Generates an AI-optimized XML-structured interpretation of a transit chart. This endpoint analyzes how the current (or future) positions of the planets affect a person's natal chart. It is essential for forecasting, understanding current life themes, and predictive astrology.

### Request Body

-   **`first_subject`** (object, required): The natal subject (the person receiving the transits). See [Subject Object Reference](../README.md#subject-object-reference).
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
-   **`transit_subject`** (object, required): The transit moment. Uses a simplified subject model — does **not** include `zodiac_type`, `sidereal_mode`, `perspective_type`, or `houses_system_identifier` (these are inherited from `first_subject`). The `name` field defaults to `"Transit"`.
    ```json
    {
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
    ```

**Transit-specific options** (optional):

-   **`include_house_comparison`** (boolean): Include house overlay comparison. Default: `true`.

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
    },
    "transit_subject": {
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 0,
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
-   **`context`** (string): The AI-optimized XML context string for the transits.
-   **`chart_data`** (object): The complete calculated transit chart data (same structure as the [Transit Chart Data](../data/chart_data_transit.md) endpoint).

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Transit\"><first_subject>Natal Subject</first_subject>...</chart_analysis>",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... },
    "aspects": [ ... ]
  }
}
```
