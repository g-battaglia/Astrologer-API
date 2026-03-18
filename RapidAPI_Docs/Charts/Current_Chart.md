## Endpoint

/api/v5/now/chart

## Name

Now: Current Datetime Birth Chart

## Description

Generates a chart for the current moment (Now) at Greenwich (UTC). Useful for getting the current planetary positions and a chart for "right now". Returns calculated data and a rendered SVG chart.

### Parameters

-   `name` (string, optional): Name for the subject (default "Now").
-   `zodiac_type` (string, optional): "Tropical" or "Sidereal".
-   `sidereal_mode` (string, optional): Sidereal mode.
-   `perspective_type` (string, optional): "Apparent Geocentric" or "Heliocentric".
-   `houses_system_identifier` (string, optional): House system code.
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
-   `show_degree_indicators` (boolean, optional): Display radial lines and degree numbers for planet positions on the chart wheel (default: true).

## Request Body Example

```json
{
    "name": "Now",
    "zodiac_type": "Tropical",
    "theme": "classic",
    "language": "EN",
    "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars"]
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Natal",
        "subject": {
            "name": "Now",
            "city": "Greenwich",
            "nation": "GB"
        },
        "aspects": []
    },
    "chart": "<svg>...</svg>"
}
```
