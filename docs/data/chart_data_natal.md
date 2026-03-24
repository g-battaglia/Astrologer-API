---
title: 'Natal Chart Data'
description: 'Access complete natal chart calculations in JSON. High-precision positions for planets, house cusps, and astrological points based on birth data.'
order: 4
---

# Natal Chart Data Endpoint

## `POST /api/v5/chart-data/birth-chart`

> **[View Complete Example](../examples/natal_chart_data)**

This endpoint returns the full calculated data for a natal chart (birth chart) without generating an SVG image. This is ideal for applications that render their own charts or need to perform deep analysis on the astrological data.

### Request Body

-   **`subject`** (object, required): The subject's birth data. See [Subject Object Reference](../README.md#subject-object-reference) for all fields.
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

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. Accepts canonical names (e.g. `"Sun"`, `"Ascendant"`) and aliases (e.g. `"asc"`, `"lilith"`). See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. Each object: `{"name": "conjunction", "orb": 10}`. Aspect names are **lowercase**. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"` for element/quality analysis.
-   **`custom_distribution_weights`** (object): Custom weights for the distribution calculation. Keys are lowercase point names, values are floats.

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
        "longitude": 2.3522,
        "latitude": 48.8566,
        "timezone": "Europe/Paris"
    },
    "distribution_method": "weighted",
    "active_aspects": [
        {"name": "conjunction", "orb": 10},
        {"name": "opposition", "orb": 10},
        {"name": "trine", "orb": 8},
        {"name": "square", "orb": 5}
    ]
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The complete chart data containing:
    -   **`subject`**: The calculated subject data (planets, houses, metadata).
    -   **`aspects`**: List of aspects between planets.
    -   **`elements_distribution`**: Analysis of Fire, Earth, Air, Water distribution.
    -   **`qualities_distribution`**: Analysis of Cardinal, Fixed, Mutable distribution.
    -   **`hemispheres_distribution`**: Analysis of chart hemispheres.

**Aspect object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `p1_name` | string | First point name (e.g. `"Sun"`). |
| `p2_name` | string | Second point name (e.g. `"Pluto"`). |
| `aspect` | string | Aspect name, **lowercase** (e.g. `"conjunction"`, `"trine"`, `"square"`). |
| `orbit` | float | Actual orb in degrees (always non-negative). |
| `aspect_degrees` | int | Exact angular distance of the aspect type (e.g. `0`, `120`, `90`). |
| `diff` | float | Actual angular distance between the two points. |
| `p1_abs_pos` | float | Absolute ecliptic longitude of first point. |
| `p2_abs_pos` | float | Absolute ecliptic longitude of second point. |
| `p1_owner` | string | Name of the subject owning the first point. |
| `p2_owner` | string | Name of the subject owning the second point. |
| `p1_speed` | float | Daily motion speed of first point in degrees. |
| `p2_speed` | float | Daily motion speed of second point in degrees. |
| `aspect_movement` | string | `"Applying"`, `"Separating"`, or `"Static"`. |

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": {
    "subject": {
      "sun": {
        "name": "Sun",
        "sign": "Sco",
        "sign_num": 7,
        "position": 2.5,
        "abs_pos": 212.5,
        "house": "Twelfth_House",
        "retrograde": false,
        "speed": 1.0133,
        "declination": -12.38,
        "magnitude": null
      }
    },
    "aspects": [
      {
        "p1_name": "Sun",
        "p2_name": "Pluto",
        "aspect": "conjunction",
        "orbit": 1.5,
        "aspect_degrees": 0,
        "aspect_movement": "Separating"
      }
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
