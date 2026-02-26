## Endpoint
/api/v5/context/synastry

## Name

Synastry Chart - AI Context

## Description

Returns a structured XML analysis of a synastry chart (relationship), optimized for AI/LLMs. Includes inter-chart aspects and house overlays.

### Parameters

-   `first_subject` (JSON object, required): The first subject's birth data.
-   `second_subject` (JSON object, required): The second subject's birth data.
-   `include_house_comparison` (boolean, optional): Include house overlay data.
-   `include_relationship_score` (boolean, optional): Include compatibility score.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
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
    }
}
```

## Response Body Example

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Synastry\">\n  <chart name=\"Partner A\">...</chart>\n  <chart name=\"Partner B\">...</chart>\n</chart_analysis>",
    "chart_data": {
        "chart_type": "Synastry"
    }
}
```
