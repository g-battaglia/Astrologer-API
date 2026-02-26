## Endpoint
/api/v5/context/subject

## Name
Astrological Subject - AI Context

## Description

Returns a structured XML analysis of a subject (planets, houses), optimized for AI/LLMs.

### Parameters

-   `subject` (JSON object, required): The subject's birth data.

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
    "subject_context": "<chart name=\"John Doe\">...</chart>",
    "subject": {
        "name": "John Doe"
    }
}
```
