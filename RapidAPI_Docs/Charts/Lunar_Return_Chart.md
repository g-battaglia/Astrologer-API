## Endpoint

/api/v5/chart/lunar-return

## Name

Lunar (Moon) Return Chart

## Description

Generates a Lunar Return chart for the return happening on or after the specified date. The Lunar Return occurs when the Moon returns to the exact position it was at the moment of birth. This chart is used to forecast trends for the month ahead. Returns calculated data and a rendered SVG chart.

### Parameters

-   `subject` (JSON object, required): The subject's natal birth data.
-   `year` (integer, required): The year for the return.
-   `month` (integer, optional): The month for the return.
-   `day` (integer, optional): Day (1-31) to start the search from. Defaults to 1. Useful for finding later returns in the same month.
-   `return_location` (JSON object, optional): The location where the subject is for the Lunar Return.
    -   `city` (string, optional)
    -   `nation` (string, optional)
    -   `longitude` (float, required)
    -   `latitude` (float, required)
    -   `timezone` (string, required)
-   `wheel_type` (string, optional): "single" or "dual". Default is "dual".
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
    "month": 11,
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
            "name": "Lunar Return Nov 2024",
            "return_type": "Lunar"
        },
        "aspects": []
    },
    "chart": "<svg>...</svg>"
}
```
