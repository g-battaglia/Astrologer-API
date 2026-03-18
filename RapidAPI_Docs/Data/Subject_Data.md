## Endpoint
/api/v5/subject

## Name

Astrological Subject Data

## Description

Calculates and returns astrological subject data (planets, houses) without any chart rendering.

### Parameters

-   `subject` (JSON object, required): The subject's birth data.
    -   `name` (string, optional)
    -   `year` (integer, required)
    -   `month` (integer, required)
    -   `day` (integer, required)
    -   `hour` (integer, required)
    -   `minute` (integer, required)
    -   `city` (string, optional)
    -   `nation` (string, optional)
    -   `longitude` (float, required)
    -   `latitude` (float, required)
    -   `timezone` (string, required)
    -   `zodiac_type` (string, optional)
    -   `sidereal_mode` (string, optional)
    -   `perspective_type` (string, optional)
    -   `houses_system_identifier` (string, optional)
    -   `custom_ayanamsa_t0` (float, optional): Julian Day number for the reference epoch (USER sidereal mode only).
    -   `custom_ayanamsa_ayan_t0` (float, optional): Ayanamsa degrees at the reference epoch (USER sidereal mode only).

## Request Body Example

```json
{
    "subject": {
        "name": "John Doe",
        "year": 1990,
        "month": 6,
        "day": 15,
        "hour": 12,
        "minute": 30,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
}
```

## Response Body Example

```json
{
    "status": "OK",
    "subject": {
        "name": "John Doe",
        "year": 1990,
        "month": 6,
        "day": 15,
        "city": "London",
        "nation": "GB",
        "ayanamsa_value": null,
        "sun": {
            "name": "Sun",
            "quality": "Mutable",
            "element": "Air",
            "sign": "Gem",
            "sign_id": 2,
            "abs_pos": 84.123,
            "house": 9,
            "retrograde": false,
            "speed": 1.0145,
            "declination": 23.12,
            "magnitude": null
        }
    }
}
```
