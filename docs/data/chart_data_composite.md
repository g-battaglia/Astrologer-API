---
title: 'Composite Chart Data'
description: 'Retrieve raw composite chart data in JSON format. Calculate midpoints between two subjects to analyze the unique purpose and destiny of a union.'
order: 6
---

# Composite Chart Data Endpoint

## `POST /api/v5/chart-data/composite`

> **📘 [View Complete Example](../examples/composite_chart_data.md)**

This endpoint calculates the composite chart for two subjects. A composite chart is a single chart derived from the midpoints of the two subjects' planetary positions. It represents the "relationship itself" as a third entity.

### Request Body

-   **`first_subject`** (object, required): First partner.
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
-   **`second_subject`** (object, required): Second partner.
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
-   **`active_points`**, **`active_aspects`** (optional overrides).

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
    }
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): The composite chart data.
    -   **`planets`**: Midpoint positions.
    -   **`houses`**: Calculated houses for the composite location/time.
    -   **`aspects`**: Aspects within the composite chart.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": {
    "planets": {
      "Sun": {
        "name": "Sun",
        "sign": "Aqu",
        "position": 15.0,
        "abs_pos": 315.0,
        "house": "10th House",
        "speed": 1.0089,
        "declination": -19.72,
        "magnitude": null
      },
      ...
    },
    "houses": [ ... ],
    "aspects": [ ... ]
  }
}
```
