---
title: 'Subject Data'
description: 'Generate an astrological subject from raw birth data. Perform high-precision ephemeris calculations for planets, houses, and axes in machine-readable JSON.'
order: 1
---

# Subject Data Endpoint

## `POST /api/v5/subject`

> **📘 [View Complete Example](../examples/subject.md)**

This endpoint allows you to create an astrological subject object from raw birth data. It performs all necessary astronomical calculations (ephemeris) to determine the positions of planets, houses, and other astrological points for the given time and location.

The returned `AstrologicalSubjectModel` contains all the calculated data required to generate charts or perform further analysis. This endpoint is useful when you need the raw calculated data without generating a visual chart.

### Request Body

The request body must contain a `subject` object with the following fields:

-   **`subject`** (object, required): The subject's birth data.
    ```json
    {
        "name": "John Doe",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 30,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P",
        "custom_ayanamsa_t0": 2451545.0,
        "custom_ayanamsa_ayan_t0": 22.46
    }
    ```

    > `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` are optional and only used when `zodiac_type` is `"Sidereal"` with `sidereal_mode` set to `"USER"`.

#### Complete Request Example

```json
{
    "subject": {
        "name": "John Doe",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 30,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P"
    }
}
```

### Response Body

The response contains the status and the fully calculated subject object.

-   **`status`** (string): "OK" on success.
-   **`subject`** (object): The calculated astrological subject.
    -   **`planets`**: Dictionary of planetary positions (Sun, Moon, Mercury, etc.).
    -   **`houses`**: List of house cusps.
    -   **`axes`**: Ascendant, Midheaven, etc.

#### Complete Response Example

```json
{
    "status": "OK",
    "subject": {
        "name": "John Doe",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 30,
        "city": "London",
        "nation": "GB",
        "lng": -0.1278,
        "lat": 51.5074,
        "tz_str": "Europe/London",
        "ayanamsa_value": null,
        "sun": {
            "name": "Sun",
            "quality": "Cardinal",
            "element": "Earth",
            "sign": "Cap",
            "sign_num": 9,
            "position": 10.5,
            "abs_pos": 280.5,
            "emoji": "♑",
            "house": "10th House",
            "retrograde": false,
            "speed": 1.0189,
            "declination": -23.01,
            "magnitude": null
        },
        "moon": {
            "name": "Moon",
            "quality": "Fixed",
            "element": "Air",
            "sign": "Aqu",
            "sign_num": 10,
            "position": 15.2,
            "abs_pos": 315.2,
            "emoji": "♒",
            "house": "11th House",
            "retrograde": false,
            "speed": 12.174,
            "declination": -14.55,
            "magnitude": null
        },
        "first_house": {
            "name": "1st House",
            "quality": "Cardinal",
            "element": "Fire",
            "sign": "Ari",
            "sign_num": 0,
            "position": 5.5,
            "abs_pos": 5.5,
            "emoji": "♈"
        }
        // ... other planets and houses
    }
}
```
