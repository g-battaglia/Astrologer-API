---
title: 'Subject Context'
description: 'Get structured birth data summaries to serve as context for AI-generated personality insights. Optimized for automated personal horoscopes with LLMs.'
order: 1
---

# Subject Context Endpoint

## `POST /api/v5/context/subject`

> **📘 [View Complete Example](../examples/subject_context.md)**

Generates an AI-powered astrological interpretation based on a subject's birth data. This endpoint provides an XML-structured analysis of the subject's key astrological placements, suitable for generating horoscopes, personality insights, or character descriptions.

It uses a Large Language Model (LLM) to synthesize the astrological data into a coherent, human-readable narrative.

### Request Body

-   **`subject`** (object, required): The subject's birth data.
    ```json
    {
        "name": "Subject Name",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
    ```

#### Complete Request Example

```json
{
    "subject": {
        "name": "Subject Name",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`subject_context`** (string): The generated AI XML context string.
-   **`subject`** (object): The calculated subject data used for the interpretation.

#### Complete Response Example

```json
{
  "status": "OK",
  "subject_context": "<chart name=\"Subject Name\">...</chart>",
  "subject": {
    "name": "Subject Name",
    "year": 1990,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "city": "London",
    "nation": "GB",
    "lng": -0.1278,
    "lat": 51.5074,
    "tz_str": "Europe/London",
    "zodiac_type": "Tropical",
    "sun": { ... },
    "moon": { ... }
    // ... full subject data
  }
}
```
