## Endpoint

/api/v5/chart/birth-chart

## Name

Birth Chart

## Description

Generates a natal chart (birth chart) for a specific person and time. Returns both the calculated astrological data and a rendered SVG chart. You can customize the visual appearance (theme, language) and calculation parameters (house system, zodiac type).

### Parameters

-   `subject` (JSON object, required): The subject's birth data.
    -   `name` (string, optional): Name of the subject.
    -   `year` (integer, required): Birth year.
    -   `month` (integer, required): Birth month (1-12).
    -   `day` (integer, required): Birth day (1-31).
    -   `hour` (integer, required): Birth hour (0-23).
    -   `minute` (integer, required): Birth minute (0-59).
    -   `city` (string, optional): City name.
    -   `nation` (string, optional): Country code (ISO 2-letter).
    -   `longitude` (float, required): Longitude (decimal degrees).
    -   `latitude` (float, required): Latitude (decimal degrees).
    -   `timezone` (string, required): IANA timezone string (e.g., "Europe/London").
    -   `zodiac_type` (string, optional): "Tropical" (default) or "Sidereal".
    -   `sidereal_mode` (string, optional): Sidereal mode if zodiac_type is Sidereal (e.g., "LAHIRI").
    -   `perspective_type` (string, optional): "Apparent Geocentric" (default) or "Heliocentric".
    -   `houses_system_identifier` (string, optional): House system code (default "P" for Placidus).
    -   `custom_ayanamsa_t0` (float, optional): Julian Day number for the reference epoch (USER sidereal mode only).
    -   `custom_ayanamsa_ayan_t0` (float, optional): Ayanamsa degrees at the reference epoch (USER sidereal mode only).
-   `theme` (string, optional): Visual theme for the chart (e.g., "classic", "dark", "light", "strawberry").
-   `language` (string, optional): Language code for chart labels (e.g., "EN", "IT", "ES").
-   `split_chart` (boolean, optional): If true, returns separate SVG strings for the wheel and the grid.
-   `transparent_background` (boolean, optional): If true, the chart background will be transparent.
-   `show_house_position_comparison` (boolean, optional): If true, includes a table comparing house positions.
-   `custom_title` (string, optional): Custom title to display on the chart.
-   `active_points` (array of strings, optional): List of planets/points to include (e.g., ["Sun", "Moon"]).
-   `active_aspects` (array of objects, optional): Configuration for aspects to include.
-   `show_aspect_icons` (boolean, optional): Display aspect icons on aspect lines (default: true).
-   `style` (string, optional): Chart wheel layout — "classic" (default) or "modern".
-   `show_zodiac_background_ring` (boolean, optional): Show colored zodiac wedges behind the wheel, modern style only (default: true).
-   `show_degree_indicators` (boolean, optional): Display radial lines and degree numbers for planet positions on the chart wheel (default: true).
-   `distribution_method` (string, optional): Method for calculating element/quality distribution ("weighted" or "pure_count").
-   `custom_distribution_weights` (JSON object, optional): Custom weights for the distribution calculation.

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
        "timezone": "Europe/London",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P"
    },
    "theme": "classic",
    "language": "EN",
    "split_chart": false,
    "transparent_background": false,
    "show_house_position_comparison": true,
    "custom_title": "John's Natal Chart",
    "active_points": [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Chiron",
        "Lilith",
        "north_node"
    ],
    "active_aspects": [
        { "name": "conjunction", "orb": 8 },
        { "name": "opposition", "orb": 8 },
        { "name": "trine", "orb": 8 },
        { "name": "square", "orb": 8 },
        { "name": "sextile", "orb": 6 }
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
            "hour": 12,
            "minute": 30,
            "city": "London",
            "nation": "GB",
            "longitude": -0.1278,
            "latitude": 51.5074,
            "timezone": "Europe/London",
            "zodiac_type": "Tropical",
            "ayanamsa_value": null
        },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Moon",
                "aspect": "trine",
                "orb": 4.2,
                "is_major": true
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
        "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
        "active_aspects": [
            { "name": "conjunction", "orb": 8 },
            { "name": "trine", "orb": 8 }
        ]
    },
    "chart": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 600 600\">...</svg>"
}
```
