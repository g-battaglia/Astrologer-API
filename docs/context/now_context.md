---
title: 'Now Context'
description: 'Obtain a real-time astrological context snapshot for AI-driven "Daily Horoscope" or "Weather" features. Formatted for immediate use with LLMs.'
order: 2
---

# Now Context Endpoint

## `POST /api/v5/now/context`

> **📘 [View Complete Example](../examples/now_context.md)**

Generates an AI-powered astrological interpretation for the **current moment** (UTC). This is ideal for "Daily Horoscope", "Current Sky", or "Astrological Weather" features, providing a real-time XML-structured snapshot of the planetary atmosphere.

It automatically calculates the positions of celestial bodies for "now" and generates a descriptive context.

### Request Body

-   **`name`** (string, optional): A custom name for the context (e.g., "Today's Vibe"). Default: "Now".
-   **`zodiac_type`** (string, optional): "Tropical" (default) or "Sidereal".
-   **`sidereal_mode`** (string, optional): Required if `zodiac_type` is "Sidereal".
-   **`houses_system_identifier`** (string, optional): House system code (default: "P").

#### Complete Request Example

```json
{
    "name": "Current Atmosphere",
    "zodiac_type": "Tropical"
}
```

### Response Body

-   **`status`** (string): "OK" on success.
-   **`subject_context`** (string): The generated AI XML context string of the current sky.
-   **`subject`** (object): The calculated subject data for the current moment.

#### Complete Response Example

```json
{
  "status": "OK",
  "subject_context": "<chart name=\"Current Atmosphere\">...</chart>",
  "subject": {
    "name": "Current Atmosphere",
    "year": 2023,
    "month": 10,
    "day": 27,
    "hour": 14,
    "minute": 30,
    "city": "Greenwich",
    "nation": "GB",
    "lng": -0.0015,
    "lat": 51.4779,
    "tz_str": "Etc/UTC",
    "sun": { ... },
    "moon": { ... }
    // ... full subject data
  }
}
```
