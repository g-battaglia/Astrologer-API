## Endpoint
/api/v5/chart-data/birth-chart

## Name

Birth Chart Data

## Description

Returns complete natal chart data (planetary positions, aspects, distributions) without SVG rendering. Use this endpoint when you only need the raw astrological data for your own processing or display.

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
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `distribution_method` (string, optional): Distribution calculation method.
-   `custom_distribution_weights` (JSON object, optional): Custom weights.

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
    },
    "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
    "active_aspects": [
        { "name": "conjunction", "orb": 8 },
        { "name": "trine", "orb": 8 }
    ]
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Natal",
        "subject": {
            "name": "John Doe",
            "year": 1990,
            "month": 6,
            "day": 15,
            "city": "London",
            "nation": "GB",
            "ayanamsa_value": null
        },
        "planets": {
            "Sun": {
                "name": "Sun",
                "sign": "Gem",
                "abs_pos": 84.123,
                "house": 9,
                "retrograde": false,
                "speed": 1.0145,
                "declination": 23.12,
                "magnitude": null
            }
        },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Moon",
                "aspect": "trine",
                "orb": 4.2
            }
        ],
        "element_distribution": {
            "fire": 25.0,
            "earth": 25.0,
            "air": 25.0,
            "water": 25.0
        },
        "quality_distribution": {
            "cardinal": 33.3,
            "fixed": 33.3,
            "mutable": 33.3
        },
        "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    }
}
```
