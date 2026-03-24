---
title: 'Now Context'
description: 'Obtain a real-time astrological context snapshot for AI-driven "Daily Horoscope" or "Weather" features. Formatted for immediate use with LLMs.'
order: 2
---

# Now Context Endpoint

## `POST /api/v5/now/context`

> **[View Complete Example](../examples/now_context)**

Generates an AI-optimized XML-structured astrological context for the **current moment** (UTC). This is ideal for "Daily Horoscope", "Current Sky", or "Astrological Weather" features, providing a real-time snapshot of the planetary atmosphere.

It automatically calculates the positions of celestial bodies for "now" at Greenwich Observatory and generates a descriptive context.

> **Note:** This endpoint returns the AI text in a field called `subject_context` (not `context`), alongside the full `subject` data. See [Response Key Naming](../README.md#response-key-naming).

This endpoint does **not** require a `subject` object — configuration fields are provided at the request body root level.

### Request Body

All fields are optional. An empty JSON object `{}` is a valid request.

-   **`name`** (string): Custom name for the context. Default: `"Now"`.
-   **`zodiac_type`** (string): `"Tropical"` (default) or `"Sidereal"`.
-   **`sidereal_mode`** (string): Ayanamsa system. Required when `zodiac_type` is `"Sidereal"`. See [Sidereal Modes](../README.md#sidereal-modes).
-   **`perspective_type`** (string): Astronomical perspective. Default: `"Apparent Geocentric"`. See [Perspective Types](../README.md#perspective-types).
-   **`houses_system_identifier`** (string): House system code. Default: `"P"` (Placidus). See [House Systems](../README.md#house-systems).

Rendering options (`theme`, `language`, `style`, `split_chart`, `transparent_background`, etc.) are **not** accepted on this endpoint.

#### Complete Request Example

```json
{
    "name": "Current Atmosphere",
    "zodiac_type": "Tropical"
}
```

### Response Body

-   **`status`** (string): `"OK"`.
-   **`subject_context`** (string): The AI-optimized XML context string of the current sky.
-   **`subject`** (object): The calculated subject data for the current moment. Same structure as the [Now Subject](../data/now_subject.md) endpoint.

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
