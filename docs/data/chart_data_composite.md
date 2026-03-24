---
title: 'Composite Chart Data'
description: 'Retrieve raw composite chart data in JSON format. Calculate midpoints between two subjects to analyze the unique purpose and destiny of a union.'
order: 6
---

# Composite Chart Data Endpoint

## `POST /api/v5/chart-data/composite`

> **[View Complete Example](../examples/composite_chart_data)**

This endpoint calculates the composite chart for two subjects without generating an SVG chart. A composite chart is a single chart derived from the midpoints of the two subjects' planetary positions. It represents the "relationship itself" as a third entity.

### Request Body

-   **`first_subject`** (object, required): First partner. See [Subject Object Reference](../README.md#subject-object-reference).
    ```json
    {
        "name": "Partner A",
        "year": 1980,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "Rome",
        "nation": "IT",
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome"
    }
    ```
-   **`second_subject`** (object, required): Second partner. Same structure as `first_subject`.
    ```json
    {
        "name": "Partner B",
        "year": 1982,
        "month": 3,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Milan",
        "nation": "IT",
        "longitude": 9.19,
        "latitude": 45.4642,
        "timezone": "Europe/Rome"
    }
    ```

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
        "year": 1980,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "Rome",
        "nation": "IT",
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome"
    },
    "second_subject": {
        "name": "Partner B",
        "year": 1982,
        "month": 3,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Milan",
        "nation": "IT",
        "longitude": 9.19,
        "latitude": 45.4642,
        "timezone": "Europe/Rome"
    },
    "distribution_method": "weighted"
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The composite chart data containing:
    -   **`subject`**: The composite subject with midpoint positions for all planets and houses.
    -   **`aspects`**: Aspects within the composite chart. Aspect names are **lowercase** (e.g. `"conjunction"`, `"trine"`).
    -   **`elements_distribution`**: Fire, Earth, Air, Water distribution.
    -   **`qualities_distribution`**: Cardinal, Fixed, Mutable distribution.
    -   **`hemispheres_distribution`**: Chart hemisphere analysis.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": {
    "subject": {
      "sun": {
        "name": "Sun",
        "sign": "Aqu",
        "sign_num": 10,
        "position": 15.0,
        "abs_pos": 315.0,
        "house": "Tenth_House",
        "retrograde": false,
        "speed": 1.0089,
        "declination": -19.72,
        "magnitude": null
      }
    },
    "aspects": [
      {
        "p1_name": "Sun",
        "p2_name": "Moon",
        "aspect": "sextile",
        "orbit": 3.2,
        "aspect_degrees": 60,
        "aspect_movement": "Applying"
      }
    ],
    "elements_distribution": { ... },
    "qualities_distribution": { ... }
  }
}
```
