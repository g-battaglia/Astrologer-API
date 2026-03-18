---
title: 'Synastry Chart Data'
description: 'Access comprehensive synastry data in JSON. High-precision inter-aspect calculations between two subjects for deep relationship compatibility analysis.'
order: 5
---

# Synastry Chart Data Endpoint

## `POST /api/v5/chart-data/synastry`

> **📘 [View Complete Example](../examples/synastry_chart_data.md)**

This endpoint calculates the synastry (relationship) data between two subjects. It returns the positions for both subjects and the inter-aspects between them.

### Request Body

-   **`first_subject`** (object, required): The "inner wheel" subject.
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
-   **`second_subject`** (object, required): The "outer wheel" subject.
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
-   **`include_house_comparison`** (bool, optional): Include house overlay analysis (default: true).
-   **`include_relationship_score`** (bool, optional): Include compatibility score (default: true).
-   **`active_points`**, **`active_aspects`** (optional overrides).

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
    }
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object):
    -   **`first_subject`**: Full chart data for person A.
    -   **`second_subject`**: Full chart data for person B.
    -   **`aspects`**: List of inter-aspects (Person A planet vs Person B planet).
    -   **`relationship_score`**: (if requested) Compatibility analysis.
    -   **`house_comparison`**: (if requested) Where Person B's planets fall in Person A's houses.

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
        "aspect": "Trine",
        "orb": 2.1
      }
    ],
    "relationship_score": {
      "score_value": 15.5,
      "score_description": "Very high compatibility...",
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
