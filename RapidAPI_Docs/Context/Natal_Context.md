## Endpoint
/api/v5/context/birth-chart

## Name
Birth Chart - AI Context

## Description

Returns a structured XML analysis of a natal chart, optimized for use with AI/LLMs. Includes planetary positions, aspects, and distributions in a format that is easy for language models to parse and interpret.

### Parameters

-   `subject` (JSON object, required): The subject's birth data.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `distribution_method` (string, optional): Distribution calculation method.
-   `custom_distribution_weights` (JSON object, optional): Custom weights.

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
    }
}
```

## Response Body Example

```json
{
    "status": "OK",
    "context": "<chart_analysis type=\"Natal\">\n  <chart name=\"John Doe\">...</chart>\n</chart_analysis>",
    "chart_data": {
        "chart_type": "Natal",
        "subject": { "name": "John Doe" }
    }
}
```
