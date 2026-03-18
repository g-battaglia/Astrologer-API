---
title: 'Now Subject'
description: 'Get real-time astrological data for the current moment. Automatic UTC calculation of planetary positions for "Astrological Weather" and live features.'
order: 2
---

# Now Subject Endpoint

## `POST /api/v5/now/subject`

> **📘 [View Complete Example](../examples/now_subject.md)**

This endpoint generates an astrological subject for the **current moment** (UTC). It is essentially a "real-time" astrology calculator. It automatically fetches the current time and sets the location to Greenwich (UTC reference) to provide a universal "now" perspective.

This is useful for:

-   Checking current planetary transits.
-   Displaying a "sky now" feature.
-   Getting the current astrological atmosphere.

### Request Body

The request body allows you to configure the calculation parameters. Since the time and location are fixed to "now" and "Greenwich", you only provide configuration options.

-   **`name`** (string, optional): A custom name for the subject (default: "Now").
-   **`zodiac_type`** (string, optional): "Tropical" (default) or "Sidereal".
-   **`sidereal_mode`** (string, optional): Required if `zodiac_type` is "Sidereal".
-   **`houses_system_identifier`** (string, optional): House system code (default: "P").

#### Complete Request Example

```json
{
    "name": "Current Sky",
    "zodiac_type": "Tropical",
    "houses_system_identifier": "P"
}
```

### Response Body

Returns the calculated subject for the current moment.

-   **`status`** (string): "OK".
-   **`subject`** (object): The calculated astrological subject.

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
        "ayanamsa_value": null,
        "sun": {
            "name": "Sun",
            "sign": "Sco",
            "position": 4.5,
            "abs_pos": 214.5,
            "emoji": "♏",
            "house": "9th House",
            "speed": 1.0067,
            "declination": -13.12
        },
        "moon": {
            "name": "Moon",
            "sign": "Ari",
            "position": 12.0,
            "abs_pos": 12.0,
            "emoji": "♈",
            "house": "2nd House",
            "speed": 13.245,
            "declination": 5.67
        }
        // ... other planets and houses
    }
}
```
