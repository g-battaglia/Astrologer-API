---
title: 'Compatibility Score'
description: 'Calculate numerical relationship compatibility scores using the Ciro Discepolo method. Includes qualitative descriptions and "Destiny Signs" analysis.'
order: 3
---

# Compatibility Score Endpoint

## `POST /api/v5/compatibility-score`

> **📘 [View Complete Example](../examples/compatibility_score.md)**

This endpoint calculates a compatibility score (Synastry) between two subjects based on Ciro Discepolo's method. It evaluates the astrological aspects between the planets of the two subjects to determine a numerical score and a qualitative description of the relationship potential.

It also checks for "Destiny Signs" relationships (e.g., same Sun sign, or specific complementary signs).

### Request Body

Requires two subject objects: `first_subject` and `second_subject`.

-   **`first_subject`** (object, required): Birth data of the first person.
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
-   **`second_subject`** (object, required): Birth data of the second person.
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
-   **`active_points`** (list, optional): Override planets to include.
-   **`active_aspects`** (list, optional): Override aspects to consider.

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
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London"
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
        "lng": -74.006,
        "lat": 40.7128,
        "tz_str": "America/New_York"
    }
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`score`** (float): The calculated compatibility score (usually between -20 and +20, though can vary).
-   **`score_description`** (string): A textual description of what the score implies (e.g., "Excellent compatibility").
-   **`is_destiny_sign`** (bool): True if the subjects share a special "Destiny Sign" connection.
-   **`aspects`** (list): List of inter-aspects between the two subjects used for the calculation.
-   **`chart_data`** (object): The full synastry chart data.

#### Complete Response Example

```json
{
  "status": "OK",
  "score": 15.5,
  "score_description": "Very high compatibility. Strong potential for a lasting relationship.",
  "is_destiny_sign": false,
  "aspects": [
    {
      "p1_name": "Sun",
      "p2_name": "Moon",
      "aspect": "Trine",
      "orb": 2.5,
      "score": 5.0
    },
    {
      "p1_name": "Venus",
      "p2_name": "Mars",
      "aspect": "Conjunction",
      "orb": 1.2,
      "score": 4.0
    }
  ],
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... }
  }
}
```
