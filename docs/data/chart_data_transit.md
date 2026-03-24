---
title: 'Transit Chart Data'
description: 'Get machine-readable transit data. Compare current planetary positions against a natal chart to identify active life themes and predictive trends.'
order: 7
---

# Transit Chart Data Endpoint

## `POST /api/v5/chart-data/transit`

> **[View Complete Example](../examples/transit_chart_data)**

This endpoint calculates transit data comparing a natal chart (inner wheel) with a transit moment (outer wheel), without generating an SVG chart. It returns the positions for both subjects and the transit-to-natal aspects.

### Request Body

-   **`first_subject`** (object, required): The natal subject. See [Subject Object Reference](../README.md#subject-object-reference).
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

-   **`include_house_comparison`** (boolean): Include house overlay comparison showing where transiting planets fall in natal houses. Default: `true`.

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

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
    },
    "include_house_comparison": true
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The transit chart data containing:
    -   **`first_subject`**: Natal chart data.
    -   **`second_subject`**: Transit chart data.
    -   **`aspects`**: Transit-to-natal aspects. Aspect names are **lowercase** (e.g. `"square"`, `"conjunction"`).
    -   **`house_comparison`** (if requested): Where transiting planets fall in natal houses.
    -   **`elements_distribution`**, **`qualities_distribution`**, **`hemispheres_distribution`**: Distribution analysis.

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
        "aspect": "square",
        "orbit": 0.5,
        "aspect_degrees": 90,
        "aspect_movement": "Applying"
      }
    ]
  }
}
```
