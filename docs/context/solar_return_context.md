---
title: 'Solar Return Context'
description: 'Obtain formatted Solar Return data and yearly summaries to power AI astrological forecasts. Ideal context for LLMs to interpret birthday chart themes.'
order: 7
---

# Solar Return Context Endpoint

## `POST /api/v5/context/solar-return`

> **[View Complete Example](../examples/solar_return_context)**

Generates an AI-optimized XML-structured interpretation of a Solar Return chart. The Solar Return occurs once a year when the Sun returns to its exact natal position. This chart is used to forecast the themes and events for the year ahead (from one birthday to the next).

### Request Body

-   **`subject`** (object, required): The natal subject. See [Subject Object Reference](../README.md#subject-object-reference).
    ```json
    {
        "name": "John Doe",
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

**Search parameters** (provide `year` or `iso_datetime`):

-   **`year`** (integer, required unless `iso_datetime` is set): Calendar year to search for the next return (1-3000).
-   **`month`** (integer, optional): Month (1-12) to start the search from. Requires `year`.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to `1`.
-   **`iso_datetime`** (string, optional): ISO 8601 formatted datetime to start the search from. E.g. `"2025-05-01T00:00:00+00:00"`. Alternative to `year`/`month`/`day`.

**Return-specific options** (optional):

-   **`wheel_type`** (string): `"dual"` (default) or `"single"`.
-   **`include_house_comparison`** (boolean): Include house overlay comparison for dual wheel. Default: `true`.
-   **`return_location`** (object, optional): Override the location for the return chart. See [Solar Return Chart](../charts/solar_return_chart.md) for the full `return_location` field reference.

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
        "name": "John Doe",
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
    "year": 2024,
    "month": 1,
    "day": 1
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`return_type`** (string): `"Solar"`.
-   **`wheel_type`** (string): `"dual"` or `"single"`.
-   **`context`** (string): The AI-optimized XML context string for the solar return.
-   **`chart_data`** (object): The complete calculated solar return chart data (same structure as the [Solar Return Data](../data/chart_data_solar_return.md) endpoint).

#### Complete Response Example

```json
{
  "status": "OK",
  "return_type": "Solar",
  "wheel_type": "dual",
  "context": "<chart_analysis type=\"Solar Return\"><subject>John Doe</subject>...</chart_analysis>",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... },
    "aspects": [ ... ]
  }
}
```
