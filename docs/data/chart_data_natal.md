---
title: 'Natal Chart Data'
description: 'Access complete natal chart calculations in JSON. High-precision positions for planets, house cusps, and astrological points based on birth data.'
order: 4
---

# Natal Chart Data Endpoint

## `POST /api/v5/chart-data/birth-chart`

> **📘 [View Complete Example](../examples/natal_chart_data.md)**

This endpoint returns the full calculated data for a natal chart (birth chart) without generating an SVG image. This is ideal for applications that render their own charts or need to perform deep analysis on the astrological data.

### Request Body

-   **`subject`** (object, required): The subject's birth data.
    ```json
    {
        "name": "Jane Doe",
        "year": 1985,
        "month": 10,
        "day": 26,
        "hour": 8,
        "minute": 15,
        "city": "Paris",
        "nation": "FR",
        "longitude": 2.3522,
        "latitude": 48.8566,
        "timezone": "Europe/Paris"
    }
    ```
-   **`active_points`** (list, optional): List of planets/points to include (e.g., ["Sun", "Moon", "Asc"]). Defaults to standard set.
-   **`active_aspects`** (list, optional): List of aspects to calculate (e.g., ["Conjunction", "Trine"]). Defaults to standard set.
-   **`distribution_method`** (string, optional): "weighted" (default) or "pure_count" for element/quality analysis.
-   **`custom_distribution_weights`** (object, optional): Custom weights for the distribution calculation.

#### Complete Request Example

```json
{
    "subject": {
        "name": "Jane Doe",
        "year": 1985,
        "month": 10,
        "day": 26,
        "hour": 8,
        "minute": 15,
        "city": "Paris",
        "nation": "FR",
        "lng": 2.3522,
        "lat": 48.8566,
        "tz_str": "Europe/Paris"
    },
    "distribution_method": "weighted"
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): The complete chart data.
    -   **`planets`**: Detailed planetary positions.
    -   **`houses`**: House cusps.
    -   **`aspects`**: List of aspects between planets.
    -   **`elements_distribution`**: Analysis of Fire, Earth, Air, Water.
    -   **`qualities_distribution`**: Analysis of Cardinal, Fixed, Mutable.
    -   **`hemispheres_distribution`**: Analysis of chart hemispheres.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": {
    "planets": {
      "Sun": {
        "name": "Sun",
        "sign": "Sco",
        "position": 2.5,
        "abs_pos": 212.5,
        "house": "12th House",
        ...
      },
      ...
    },
    "houses": [ ... ],
    "aspects": [
      {
        "p1_name": "Sun",
        "p2_name": "Pluto",
        "aspect": "Conjunction",
        "orb": 1.5,
        "type": "major"
      },
      ...
    ],
    "elements_distribution": {
      "Fire": 25.0,
      "Earth": 15.0,
      "Air": 20.0,
      "Water": 40.0
    },
    "qualities_distribution": { ... }
  }
}
```
