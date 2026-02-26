## Endpoint
/api/v5/context/transit

## Name

Transit Chart - AI Context

## Description

Returns a structured XML analysis of a transit chart (current planets vs natal chart), optimized for AI/LLMs.

### Parameters

-   `first_subject` (JSON object, required): The natal subject's birth data.
-   `transit_subject` (JSON object, required): The transit time and location data.
-   `include_house_comparison` (boolean, optional): Include house overlay data.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `distribution_method` (string, optional): Distribution calculation method.

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
    }
}
```

## Response Body Example

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Transit\">\n  <chart name=\"John Doe\">...</chart>\n  <chart name=\"Now\">...</chart>\n</chart_analysis>",
    "chart_data": {
        "chart_type": "Transit"
    }
}
```
