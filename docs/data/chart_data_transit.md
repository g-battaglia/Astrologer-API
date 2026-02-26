---
title: 'Transit Chart Data'
description: 'Get machine-readable transit data. Compare current planetary positions against a natal chart to identify active life themes and predictive trends.'
order: 7
---

# Transit Chart Data Endpoint

## `POST /api/v5/chart-data/transit`

> **📘 [View Complete Example](../examples/transit_chart_data.md)**

This endpoint calculates the transits for a specific subject at a specific time. It compares the natal chart (inner wheel) with the transit chart (outer wheel, current sky).

### Request Body

-   **`first_subject`** (object, required): The natal subject.
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
-   **`transit_subject`** (object, required): The transit moment (time and location).
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
-   **`include_house_comparison`** (bool, optional): Check where transiting planets fall in natal houses.

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

-   **`status`** (string): "OK".
-   **`chart_data`** (object):
    -   **`first_subject`**: Natal chart.
    -   **`second_subject`**: Transit chart.
    -   **`aspects`**: Transit-to-Natal aspects.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... },
    "aspects": [
      {
        "p1_name": "Sun",
        "p2_name": "Saturn",
        "aspect": "Square",
        "orb": 0.5
      }
    ]
  }
}
```
