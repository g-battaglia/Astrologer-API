---
title: 'Subject Context'
description: 'Get structured birth data summaries to serve as context for AI-generated personality insights. Optimized for automated personal horoscopes with LLMs.'
order: 1
---

# Subject Context Endpoint

## `POST /api/v5/context/subject`

> **[View Complete Example](../examples/subject_context)**

Generates an AI-optimized XML-structured astrological context based on a subject's birth data. This endpoint provides a structured analysis of the subject's key astrological placements, suitable for feeding into Large Language Models (LLMs) to generate horoscopes, personality insights, or character descriptions.

> **Note:** This endpoint returns the AI text in a field called `subject_context` (not `context`), alongside the full `subject` data. See [Response Key Naming](../README.md#response-key-naming).

### Request Body

-   **`subject`** (object, required): The subject's birth data. See [Subject Object Reference](../README.md#subject-object-reference).
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

**Computation options** (optional, at request body root level):

-   **`active_points`** (array of strings): Override which celestial points are included. See [Active Points](../README.md#active-points).

> **Note:** The request model also accepts `active_aspects`, `distribution_method`, and `custom_distribution_weights` fields (via shared model inheritance), but these have **no effect** on this endpoint — it builds a subject, not chart data. Only `active_points` is used.

Rendering options (`theme`, `language`, `style`, `split_chart`, `transparent_background`, etc.) are **not** accepted on this endpoint.

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

-   **`status`** (string): `"OK"`.
-   **`subject_context`** (string): The AI-optimized XML context string. This field is named `subject_context` (not `context`) because this endpoint returns a subject rather than chart data.
-   **`subject`** (object): The calculated subject data used for the interpretation. Same structure as the [Subject Data](../data/subject.md) endpoint.

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
