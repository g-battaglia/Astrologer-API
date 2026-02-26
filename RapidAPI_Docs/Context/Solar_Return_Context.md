## Endpoint

/api/v5/context/solar-return

## Name

Solar Return - AI Context

## Description

Returns a structured XML analysis of a Solar Return chart, optimized for AI/LLMs.

### Parameters

-   `subject` (JSON object, required): The subject's natal birth data.
-   `year` (integer, required): The year for the return.
-   `month` (integer, optional): Month (1-12) to start the search from.
-   `day` (integer, optional): Day (1-31) to start the search from. Defaults to 1.
-   `return_location` (JSON object, optional): The location where the subject is for the Solar Return.
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
    "month": 6,
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
    "context": "<chart_analysis type=\"DualReturnChart\">\n  <chart name=\"John Doe\">...</chart>\n  <chart name=\"Solar Return 2024\">...</chart>\n</chart_analysis>",
    "chart_data": {
        "chart_type": "DualReturnChart",
        "return_type": "Solar"
    }
}
```
