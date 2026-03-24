---
title: 'Lunar Return Chart Data'
description: 'Retrieve raw Lunar Return data in JSON. High-precision calculations for the Moon''s monthly return to its natal position for emotional forecasting.'
order: 9
---

# Lunar Return Chart Data Endpoint

## `POST /api/v5/chart-data/lunar-return`

> **[View Complete Example](../examples/lunar_return_chart_data)**

Calculates the Lunar Return chart for the return happening on or after the specified date, without generating an SVG chart. The Lunar Return occurs when the Moon returns to the exact same ecliptic longitude as in the natal chart (approximately every 27.3 days).

### Request Body

-   **`subject`** (object, required): Natal subject. See [Subject Object Reference](../README.md#subject-object-reference).
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

**Search parameters** (provide `year` or `iso_datetime`):

-   **`year`** (integer, required unless `iso_datetime` is set): Calendar year to search for the next return (1-3000).
-   **`month`** (integer, optional): Month (1-12) to start the search from. Requires `year`.
-   **`day`** (integer, optional): Day (1-31) to start the search from. Defaults to `1`. Useful for finding the second Lunar Return in a month.
-   **`iso_datetime`** (string, optional): ISO 8601 formatted datetime to start the search from. E.g. `"2025-05-01T00:00:00+00:00"`. Alternative to `year`/`month`/`day`.

**Return-specific options** (optional):

-   **`wheel_type`** (string): `"dual"` (default) or `"single"`.
    -   `"dual"`: Returns both natal and return charts (bi-wheel data model with `first_subject` and `second_subject`).
    -   `"single"`: Returns only the return chart (single chart data model with `subject`).
-   **`include_house_comparison`** (boolean): Include house overlay comparison for dual wheel. Default: `true`. Automatically set to `false` when `wheel_type` is `"single"`.
-   **`return_location`** (object, optional): Override the location for the return chart. If omitted, the natal subject's location is used.

    | Field | Type | Description |
    |-------|------|-------------|
    | `city` | string | Target city name. Falls back to natal city if omitted. |
    | `nation` | string | Two-letter ISO country code. Falls back to natal nation if omitted. |
    | `longitude` | float | Longitude (-180 to 180). |
    | `latitude` | float | Latitude (-90 to 90). |
    | `timezone` | string | IANA timezone identifier. |
    | `altitude` | float | Altitude in meters. |
    | `geonames_username` | string | GeoNames username to resolve location from city/nation. |

    Provide all three of `latitude`, `longitude`, and `timezone` for offline mode, or use `geonames_username` for online resolution.

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).
-   **`active_aspects`** (array of objects): Override which aspects are calculated and their orbs. See [Active Aspects](../README.md#active-aspects).
-   **`distribution_method`** (string): `"weighted"` (default) or `"pure_count"`.
-   **`custom_distribution_weights`** (object): Custom weights map for weighted distribution.

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
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    },
    "year": 2024,
    "month": 5,
    "day": 1,
    "wheel_type": "single"
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`chart_data`** (object): The chart data. Structure depends on `wheel_type`:
    -   **Dual** (`wheel_type: "dual"`): Contains `first_subject` (natal), `second_subject` (return), `aspects`, `house_comparison`, distribution data.
    -   **Single** (`wheel_type: "single"`): Contains `subject` (return only), `aspects`, distribution data.

#### Complete Response Example (Single)

```json
{
  "status": "OK",
  "chart_data": {
    "subject": {
      "sun": {
        "name": "Sun",
        "sign": "Tau",
        "sign_num": 1,
        "position": 12.3,
        "abs_pos": 42.3,
        "house": "Third_House",
        "retrograde": false,
        "speed": 0.9612,
        "declination": 17.45,
        "magnitude": null
      }
    },
    "aspects": [ ... ],
    "elements_distribution": { ... },
    "qualities_distribution": { ... }
  }
}
```
