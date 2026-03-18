## Endpoint

/api/v5/chart/composite

## Name

Composite Chart

## Description

Generates a midpoint composite chart for two subjects. This chart represents the relationship itself as a third entity, calculated by finding the midpoints between the planets of the two subjects. Returns calculated data and a rendered SVG chart.

### Parameters

-   `first_subject` (JSON object, required): The first subject's birth data.
-   `second_subject` (JSON object, required): The second subject's birth data.
-   `theme` (string, optional): Visual theme.
-   `language` (string, optional): Language code.
-   `split_chart` (boolean, optional): Return separate wheel and grid SVGs.
-   `transparent_background` (boolean, optional): Transparent background.
-   `show_house_position_comparison` (boolean, optional): Include house comparison table.
-   `custom_title` (string, optional): Custom title.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `show_aspect_icons` (boolean, optional): Display aspect icons on aspect lines (default: true).
-   `double_chart_aspect_grid_type` (string, optional): Aspect display layout — "list" (default) or "table".
-   `style` (string, optional): Chart wheel layout — "classic" (default) or "modern".
-   `show_zodiac_background_ring` (boolean, optional): Show colored zodiac wedges behind the wheel, modern style only (default: true).
-   `show_degree_indicators` (boolean, optional): Display radial lines and degree numbers for planet positions on the chart wheel (default: true).
-   `distribution_method` (string, optional): Distribution calculation method.

## Request Body Example

```json
{
    "first_subject": {
        "name": "Person A",
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
        "name": "Person B",
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
    "language": "EN"
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Composite",
        "subject": {
            "name": "Composite"
        },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Moon",
                "aspect": "conjunction",
                "orb": 1.2
            }
        ]
    },
    "chart": "<svg>...</svg>"
}
```
