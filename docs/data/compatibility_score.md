---
title: 'Compatibility Score'
description: 'Calculate numerical relationship compatibility scores using the Ciro Discepolo method. Includes qualitative descriptions and "Destiny Signs" analysis.'
order: 3
---

# Compatibility Score Endpoint

## `POST /api/v5/compatibility-score`

> **[View Complete Example](../examples/compatibility_score)**

This endpoint calculates a compatibility score (synastry) between two subjects based on Ciro Discepolo's method. It evaluates the astrological aspects between the planets of the two subjects to determine a numerical score and a qualitative description of the relationship potential.

It also checks for "Destiny Signs" relationships (e.g., same Sun sign, or specific complementary signs).

### Request Body

-   **`first_subject`** (object, required): Birth data of the first person. See [Subject Object Reference](../README.md#subject-object-reference).
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
-   **`second_subject`** (object, required): Birth data of the second person. Same structure as `first_subject`.
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
-   **`include_relationship_score`** (boolean): Include compatibility score. Default: `true`.

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

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
-   **`score`** (float): The calculated compatibility score.
-   **`score_description`** (string): Qualitative description. One of: `"Minimal"`, `"Medium"`, `"Important"`, `"Very Important"`, `"Exceptional"`, `"Rare Exceptional"`.
-   **`is_destiny_sign`** (boolean): `true` if the subjects share a "Destiny Sign" connection.
-   **`aspects`** (array): List of inter-aspects used in the score calculation. Each aspect includes `p1_name`, `p2_name`, `aspect` (lowercase), and `orbit`.
-   **`score_breakdown`** (array): Detailed breakdown of scoring rules and points. Each item includes `rule`, `description`, `points`, `details`.
-   **`chart_data`** (object): The full synastry chart data (same structure as [Synastry Chart Data](chart_data_synastry.md)).

#### Complete Response Example

```json
{
  "status": "OK",
  "score": 15,
  "score_description": "Very Important",
  "is_destiny_sign": false,
  "aspects": [
    {
      "p1_name": "Sun",
      "p2_name": "Moon",
      "aspect": "trine",
      "orbit": 2.5
    },
    {
      "p1_name": "Venus",
      "p2_name": "Mars",
      "aspect": "conjunction",
      "orbit": 1.2
    }
  ],
  "score_breakdown": [
    {
      "rule": "sun_moon_major",
      "description": "Sun-Moon Trine (standard)",
      "points": 5,
      "details": "Sun-Moon Trine (orbit: 2.5°)"
    }
  ],
  "chart_data": {
    "first_subject": { ... },
    "second_subject": { ... }
  }
}
```
