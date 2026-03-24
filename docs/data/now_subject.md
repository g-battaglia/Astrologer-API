---
title: 'Now Subject'
description: 'Get real-time astrological data for the current moment. Automatic UTC calculation of planetary positions for "Astrological Weather" and live features.'
order: 2
---

# Now Subject Endpoint

## `POST /api/v5/now/subject`

> **[View Complete Example](../examples/now_subject)**

This endpoint generates an astrological subject for the **current moment** (UTC). It automatically fetches the current time and sets the location to Greenwich Observatory to provide a universal "now" perspective.

This is useful for:

-   Checking current planetary transits
-   Displaying a "sky now" feature
-   Getting the current astrological atmosphere

This endpoint does **not** require a `subject` object — configuration fields are provided at the request body root level.

### Request Body

All fields are optional. An empty JSON object `{}` is a valid request.

-   **`name`** (string): Custom name for the subject. Default: `"Now"`.
-   **`zodiac_type`** (string): `"Tropical"` (default) or `"Sidereal"`.
-   **`sidereal_mode`** (string): Ayanamsa system. Required when `zodiac_type` is `"Sidereal"`. See [Sidereal Modes](../README.md#sidereal-modes).
-   **`perspective_type`** (string): Astronomical perspective. Default: `"Apparent Geocentric"`. See [Perspective Types](../README.md#perspective-types).
-   **`houses_system_identifier`** (string): House system code. Default: `"P"` (Placidus). See [House Systems](../README.md#house-systems).

#### Complete Request Example

```json
{
    "name": "Current Sky",
    "zodiac_type": "Tropical",
    "houses_system_identifier": "P"
}
```

### Response Body

Returns the calculated subject for the current moment. The response structure is identical to the [Subject Data](subject.md) endpoint.

-   **`status`** (string): `"OK"`.
-   **`subject`** (object): The calculated astrological subject. See [Subject Data](subject.md) for the full response field reference.

Key differences from `/api/v5/subject`:

-   Date/time is always the **current UTC moment** (not user-specified).
-   Location is always **Greenwich Observatory** (51.4779°N, 0.0015°W).
-   Timezone is always **`Etc/UTC`**.

#### Complete Response Example

```json
{
    "status": "OK",
    "subject": {
        "name": "Current Sky",
        "year": 2023,
        "month": 10,
        "day": 27,
        "hour": 14,
        "minute": 30,
        "city": "Greenwich",
        "nation": "GB",
        "lng": -0.0015,
        "lat": 51.4779,
        "tz_str": "Etc/UTC",
        "zodiac_type": "Tropical",
        "ayanamsa_value": null,
        "sun": {
            "name": "Sun",
            "quality": "Fixed",
            "element": "Water",
            "sign": "Sco",
            "sign_num": 7,
            "position": 4.5,
            "abs_pos": 214.5,
            "emoji": "♏",
            "house": "Ninth_House",
            "retrograde": false,
            "speed": 1.0067,
            "declination": -13.12,
            "magnitude": null
        },
        "moon": {
            "name": "Moon",
            "quality": "Cardinal",
            "element": "Fire",
            "sign": "Ari",
            "sign_num": 0,
            "position": 12.0,
            "abs_pos": 12.0,
            "emoji": "♈",
            "house": "Second_House",
            "retrograde": false,
            "speed": 13.245,
            "declination": 5.67,
            "magnitude": null
        }
        // ... other planets and houses
    }
}
```
