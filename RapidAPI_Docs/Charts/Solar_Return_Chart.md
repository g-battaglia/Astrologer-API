## Endpoint

/api/v5/chart/solar-return

## Name

Solar Return Chart

## Description

Generates a Solar Return chart for the return happening on or after the specified date. The Solar Return occurs when the Sun returns to the exact position it was at the moment of birth. This chart is used to forecast trends for the year ahead. Returns calculated data and a rendered SVG chart (can be single wheel or dual wheel with natal).

### Parameters

-   `subject` (JSON object, required): The subject's natal birth data.
-   `year` (integer, required): The year for which to calculate the Solar Return.
-   `month` (integer, optional): Month (1-12) to start the search from.
-   `day` (integer, optional): Day (1-31) to start the search from. Defaults to 1.
-   `return_location` (JSON object, optional): The location where the subject is for the Solar Return (defaults to birth location if not provided).
    -   `city` (string, optional)
    -   `nation` (string, optional)
    -   `longitude` (float, required)
    -   `latitude` (float, required)
    -   `timezone` (string, required)
-   `wheel_type` (string, optional): "single" (just the return chart) or "dual" (return chart around natal chart). Default is "dual".
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
    "year": 2024,
    "month": 6,
    "day": 1,
    "return_location": {
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    },
    "wheel_type": "dual",
    "theme": "classic",
    "language": "EN"
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "DualReturnChart",
        "first_subject": {
            "name": "John Doe"
        },
        "second_subject": {
            "name": "Solar Return 2024",
            "return_type": "Solar"
        },
        "aspects": []
    },
    "chart": "<svg>...</svg>"
}
```
