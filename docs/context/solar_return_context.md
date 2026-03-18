---
title: 'Solar Return Context'
description: 'Obtain formatted Solar Return data and yearly summaries to power AI astrological forecasts. Ideal context for LLMs to interpret birthday chart themes.'
order: 7
---

# Solar Return Context Endpoint

## `POST /api/v5/context/solar-return`

> **📘 [View Complete Example](../examples/solar_return_context.md)**

Generates an AI-powered interpretation of a Solar Return chart. The Solar Return occurs once a year when the Sun returns to its exact natal position. This chart is used to forecast the themes and events for the year ahead (from one birthday to the next).

### Request Body

-   **`subject`** (object, required): The Natal Subject.
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
-   **`year`** (integer, required): The year for which to calculate the return (e.g., 2024 for the 2024-2025 birthday year).
-   **`month`** (integer, optional): Month (1-12) to start the search from.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to 1.
-   **`return_location`** (object, optional): Location where the subject spends their birthday (relocation).
-   **Computation options**: `active_points`, `active_aspects`, `distribution_method`, `custom_distribution_weights` (identical to `/api/v5/chart-data/solar-return`). Rendering options such as `theme`, `language`, `style`, `show_zodiac_background_ring`, `double_chart_aspect_grid_type`, `split_chart`, `transparent_background`, `show_house_position_comparison`, `show_cusp_position_comparison`, `show_degree_indicators`, `show_aspect_icons`, `custom_title` are **not** accepted here.

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

-   **`status`** (string): "OK" on success.
-   **`context`** (string): The generated AI XML context string for the solar return.
-   **`chart_data`** (object): The complete calculated solar return chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "context": "<chart_analysis type=\"Solar Return\"><subject>John Doe</subject>...</chart_analysis>",
  "chart_data": {
    "natal_subject": { ... },
    "return_subject": { ... },
    "aspects_list": [ ... ]
    // ... full return data
  }
}
```
