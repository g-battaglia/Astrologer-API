## Endpoint

/api/v5/chart/transit

## Name

Transit Chart

## Description

Generates a transit chart showing the current planetary positions in relation to a natal chart. Returns calculated transit data and a rendered dual-wheel SVG chart (inner wheel: natal, outer wheel: transit).

### Parameters

-   `first_subject` (JSON object, required): The natal subject's birth data (inner wheel).
-   `transit_subject` (JSON object, required): The transit time and location data (outer wheel).
    -   `name` (string, optional): Name for the transit (e.g., "Transit").
    -   `year` (integer, required): Transit year.
    -   `month` (integer, required): Transit month.
    -   `day` (integer, required): Transit day.
    -   `hour` (integer, required): Transit hour.
    -   `minute` (integer, required): Transit minute.
    -   `city` (string, optional): City name.
    -   `nation` (string, optional): Country code.
    -   `longitude` (float, required): Longitude.
    -   `latitude` (float, required): Latitude.
    -   `timezone` (string, required): Timezone.
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

## Request Body Example

```json
{
    "first_subject": {
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
    "transit_subject": {
        "name": "Now",
        "year": 2023,
        "month": 10,
        "day": 27,
        "hour": 9,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    },
    "theme": "classic",
    "language": "EN"
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Transit",
        "first_subject": {
            "name": "John Doe"
        },
        "second_subject": {
            "name": "Now"
        },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Mars",
                "aspect": "square",
                "orb": 1.5
            }
        ]
    },
    "chart": "<svg>...</svg>"
}
```
