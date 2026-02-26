---
title: 'Solar Return Chart Data'
description: 'Retrieve raw Solar Return data. Precise calculations for the astrological birthday to forecast themes and events for the year ahead.'
order: 8
---

# Solar Return Chart Data Endpoint

## `POST /api/v5/chart-data/solar-return`

> **📘 [View Complete Example](../examples/solar_return_chart_data.md)**

Calculates the Solar Return chart for the return happening on or after the specified date. The Solar Return occurs when the Sun returns to the exact same position (longitude) as in the natal chart.

### Request Body

-   **`subject`** (object, required): Natal subject.
    ```json
    {
        "name": "John Doe",
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
-   **`year`** (integer, required): The year for which to calculate the return.
-   **`month`** (integer, optional): Month (1-12) to start the search from.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to 1.
-   **`return_location`** (object, optional): Location where the subject spends the return (relocation). If omitted, uses natal location.
-   **`wheel_type`** (string, optional): "dual" (default) or "single".
    -   "dual": Returns both natal and return charts (bi-wheel data).
    -   "single": Returns only the return chart.

#### Complete Request Example

```json
{
    "subject": {
        "name": "John Doe",
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
    "year": 2024,
    "month": 1,
    "day": 1,
    "return_location": {
        "city": "Paris",
        "nation": "FR",
        "longitude": 2.3522,
        "latitude": 48.8566,
        "timezone": "Europe/Paris"
    }
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`return_type`** (string): "Solar".
-   **`wheel_type`** (string): "dual" or "single".
-   **`chart_data`** (object): Single or Dual chart data structure.

#### Complete Response Example

```json
{
  "status": "OK",
  "return_type": "Solar",
  "wheel_type": "dual",
  "chart_data": {
    "first_subject": { ... }, // Natal
    "second_subject": { ... }, // Solar Return
    "aspects": [ ... ]
  }
}
```
