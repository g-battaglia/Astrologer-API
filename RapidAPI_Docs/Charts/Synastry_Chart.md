## Endpoint

/api/v5/chart/synastry

## Name

Synastry Chart

## Description

Generates a synastry chart (relationship chart) comparing two subjects. Returns calculated compatibility data and a rendered dual-wheel SVG chart. This chart visualizes the geometric relationships (aspects) between the planets of two different people.

### Parameters

-   `first_subject` (JSON object, required): The first subject's birth data (inner wheel).
    -   `name` (string, optional): Name of the subject.
    -   `year` (integer, required): Birth year.
    -   `month` (integer, required): Birth month.
    -   `day` (integer, required): Birth day.
    -   `hour` (integer, required): Birth hour.
    -   `minute` (integer, required): Birth minute.
    -   `city` (string, optional): City name.
    -   `nation` (string, optional): Country code.
    -   `longitude` (float, required): Longitude.
    -   `latitude` (float, required): Latitude.
    -   `timezone` (string, required): Timezone.
    -   `zodiac_type` (string, optional): "Tropical" or "Sidereal".
    -   `houses_system_identifier` (string, optional): House system code.
-   `second_subject` (JSON object, required): The second subject's birth data (outer wheel). Same structure as `first_subject`.
-   `theme` (string, optional): Visual theme.
-   `language` (string, optional): Language code.
-   `split_chart` (boolean, optional): Return separate wheel and grid SVGs.
-   `transparent_background` (boolean, optional): Transparent background.
-   `show_house_position_comparison` (boolean, optional): Include house comparison table.
-   `custom_title` (string, optional): Custom title.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `show_aspect_icons` (boolean, optional): Display aspect icons on aspect lines (default: true).
-   `style` (string, optional): Chart wheel layout — "classic" (default) or "modern".
-   `show_zodiac_background_ring` (boolean, optional): Show colored zodiac wedges behind the wheel, modern style only (default: true).
-   `double_chart_aspect_grid_type` (string, optional): Aspect display for dual charts — "list" (default) or "table".
-   `show_degree_indicators` (boolean, optional): Display radial lines and degree numbers for planet positions on the chart wheel (default: true).
-   `show_cusp_position_comparison` (boolean, optional): Include the cusp position comparison table for dual charts (default: true).
-   `distribution_method` (string, optional): Distribution calculation method.

## Request Body Example

```json
{
    "first_subject": {
        "name": "Partner A",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    },
    "second_subject": {
        "name": "Partner B",
        "year": 1992,
        "month": 5,
        "day": 20,
        "hour": 18,
        "minute": 30,
        "city": "Los Angeles",
        "nation": "US",
        "longitude": -118.2437,
        "latitude": 34.0522,
        "timezone": "America/Los_Angeles"
    },
    "theme": "classic",
    "language": "EN",
    "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
    "active_aspects": [
        { "name": "conjunction", "orb": 8 },
        { "name": "opposition", "orb": 8 }
    ]
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Synastry",
        "first_subject": {
            "name": "Partner A"
        },
        "second_subject": {
            "name": "Partner B"
        },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Moon",
                "aspect": "conjunction",
                "orb": 2.5
            }
        ],
        "house_comparison": {
            "first_points_in_second_houses": [],
            "second_points_in_first_houses": []
        },
        "relationship_score": {
            "score_value": 25,
            "score_description": "Exceptional",
            "is_destiny_sign": false
        }
    },
    "chart": "<svg>...</svg>"
}
```
