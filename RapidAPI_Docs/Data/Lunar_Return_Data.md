## Endpoint

/api/v5/chart-data/lunar-return

## Name

Lunar Return Data

## Description

Calculates Lunar Return chart data for the return happening on or after the specified date. Does not include SVG rendering.

### Parameters

-   `subject` (JSON object, required): The subject's natal birth data.
-   `year` (integer, required): The year for the return.
-   `month` (integer, optional): The month for the return.
-   `day` (integer, optional): Day (1-31) to start the search from. Defaults to 1. Useful for finding later returns in the same month.
-   `return_location` (JSON object, optional): The location where the subject is for the Lunar Return.
-   `wheel_type` (string, optional): "single" or "dual".
-   `include_house_comparison` (boolean, optional): Include house comparison table.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `distribution_method` (string, optional): Distribution calculation method.

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
    "day": 15,
    "return_location": {
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    },
    "wheel_type": "dual"
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "DualReturnChart",
        "first_subject": { "name": "John Doe" },
        "second_subject": {
            "name": "Lunar Return Nov 2024",
            "return_type": "Lunar"
        },
        "aspects": []
    }
}
```
