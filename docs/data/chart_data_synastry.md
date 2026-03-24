---
title: 'Synastry Chart Data'
description: 'Access comprehensive synastry data in JSON. High-precision inter-aspect calculations between two subjects for deep relationship compatibility analysis.'
order: 5
---

# Synastry Chart Data Endpoint

## `POST /api/v5/chart-data/synastry`

> **[View Complete Example](../examples/synastry_chart_data)**

This endpoint calculates the synastry (relationship) data between two subjects. It returns the positions for both subjects and the inter-aspects between them, without generating an SVG chart.

### Request Body

-   **`first_subject`** (object, required): The "inner wheel" subject. See [Subject Object Reference](../README.md#subject-object-reference).
    ```json
    {
        "name": "Person A",
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
-   **`second_subject`** (object, required): The "outer wheel" subject. Same structure as `first_subject`.
    ```json
    {
        "name": "Person B",
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

#### Complete Request Example

```json
{
    "first_subject": {
        "name": "Person A",
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
        "name": "Person B",
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
    },
    "include_relationship_score": true
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The synastry chart data containing:
    -   **`first_subject`**: Full chart data for Person A.
    -   **`second_subject`**: Full chart data for Person B.
    -   **`aspects`**: List of inter-aspects (Person A planets vs Person B planets). Aspect names are **lowercase** (e.g. `"trine"`, `"conjunction"`).
    -   **`relationship_score`** (if requested): Compatibility analysis containing `score_value`, `score_description`, `is_destiny_sign`, `aspects`, and `score_breakdown`.
    -   **`house_comparison`** (if requested): Where each person's planets fall in the other's houses.
    -   **`elements_distribution`**, **`qualities_distribution`**, **`hemispheres_distribution`**: Distribution analysis.

**Relationship score fields:**

| Field | Type | Description |
|-------|------|-------------|
| `score_value` | int | Numerical compatibility score. |
| `score_description` | string | One of: `"Minimal"`, `"Medium"`, `"Important"`, `"Very Important"`, `"Exceptional"`, `"Rare Exceptional"`. |
| `is_destiny_sign` | boolean | Whether the subjects form a destiny-sign relationship. |
| `aspects` | array | Aspects used in the score calculation. |
| `score_breakdown` | array | Breakdown of scoring rules and points. Each item has `rule`, `description`, `points`, `details`. |

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
        "p2_name": "Moon",
        "aspect": "trine",
        "orbit": 2.1,
        "aspect_degrees": 120,
        "aspect_movement": "Separating"
      }
    ],
    "relationship_score": {
      "score_value": 15,
      "score_description": "Very Important",
      "is_destiny_sign": false,
      "aspects": [ ... ],
      "score_breakdown": [
        {
          "rule": "sun_sun_major",
          "description": "Sun-Sun Trine (standard)",
          "points": 8,
          "details": "Sun-Sun Trine (orbit: 2.1°)"
        }
      ]
    }
  }
}
```
