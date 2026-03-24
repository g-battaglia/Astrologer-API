---
title: 'Subject Data'
description: 'Generate an astrological subject from raw birth data. Perform high-precision ephemeris calculations for planets, houses, and axes in machine-readable JSON.'
order: 1
---

# Subject Data Endpoint

## `POST /api/v5/subject`

> **[View Complete Example](../examples/subject)**

This endpoint creates an astrological subject object from raw birth data. It performs all necessary astronomical calculations (ephemeris) to determine the positions of planets, houses, and other astrological points for the given time and location.

The returned `AstrologicalSubjectModel` contains all the calculated data required to generate charts or perform further analysis. This endpoint is useful when you need the raw calculated data without generating a visual chart.

### Request Body

-   **`subject`** (object, required): The subject's birth data. See [Subject Object Reference](../README.md#subject-object-reference) for all fields.
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
        "perspective_type": "Apparent Geocentric"
    }
    ```

    > For Sidereal calculations, set `zodiac_type` to `"Sidereal"` and provide `sidereal_mode` (e.g. `"LAHIRI"`). For a custom ayanamsa, set `sidereal_mode` to `"USER"` and provide `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0`.

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).

> **Note:** The request model also accepts `active_aspects`, `distribution_method`, and `custom_distribution_weights` fields (via shared model inheritance), but these have **no effect** on this endpoint — it builds a subject, not chart data. Only `active_points` is used.

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

-   **`status`** (string): `"OK"`.
-   **`subject`** (object): The calculated astrological subject containing:
    -   **Planetary positions** (`sun`, `moon`, `mercury`, etc.): Each planet object includes `name`, `quality`, `element`, `sign`, `sign_num`, `position`, `abs_pos`, `emoji`, `house`, `retrograde`, `speed`, `declination`, `magnitude`.
    -   **House cusps** (`first_house` through `twelfth_house`): Each includes `name`, `quality`, `element`, `sign`, `sign_num`, `position`, `abs_pos`, `emoji`.
    -   **Metadata**: `name`, `year`, `month`, `day`, `hour`, `minute`, `city`, `nation`, `lng`, `lat`, `tz_str`, `zodiac_type`, `houses_system_identifier`, `perspective_type`, `ayanamsa_value`.

**Response field details:**

| Field | Description |
|-------|-------------|
| `sign` | Three-letter zodiac sign abbreviation. See [Sign Abbreviations](../README.md#sign-abbreviations). |
| `sign_num` | Zero-indexed sign number (Aries=0 through Pisces=11). |
| `position` | Degrees within the sign (0-30). |
| `abs_pos` | Absolute ecliptic longitude (0-360). |
| `house` | House placement (e.g. `"First_House"`, `"Tenth_House"`). |
| `retrograde` | `true` if the planet is retrograde. |
| `speed` | Daily motion in degrees. |
| `declination` | Declination in degrees. |
| `magnitude` | Visual magnitude (null for Sun, Moon, and calculated points). |

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
        "zodiac_type": "Tropical",
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
            "house": "Tenth_House",
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
            "house": "Eleventh_House",
            "retrograde": false,
            "speed": 12.174,
            "declination": -14.55,
            "magnitude": null
        },
        "first_house": {
            "name": "First_House",
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
