---
title: 'Moon Phase Context'
description: 'Get detailed moon phase data with AI-optimized XML context for LLM integration. Includes phase, illumination, eclipses, and sun data.'
order: 9
---

# Moon Phase Context Endpoint

## `POST /api/v5/moon-phase/context`

> **[View Complete Example](../examples/moon_phase_context)**

Returns detailed moon phase information with an AI-optimized XML context string, suitable for LLM consumption. This is the context variant of `/api/v5/moon-phase`.

Unlike other context endpoints, this uses a **simplified flat request model** -- no `subject` wrapper, no `name`, `city`, or `nation` fields. Only date/time and geographic coordinates are required.

**Important:** This endpoint uses strict validation. Unknown/extra fields (e.g., `name`, `city`, `nation`) in the request body will be rejected with a `422` error.

### Use Cases

-   Providing lunar phase data to AI/LLM for interpretation.
-   Building AI-powered moon phase reading features.
-   Enriching astrological AI prompts with lunar context.

### Request Body

The request body is identical to `/api/v5/moon-phase`:

-   **`year`** (integer, required): Year of the event (1-3000).
-   **`month`** (integer, required): Month (1-12).
-   **`day`** (integer, required): Day (1-31).
-   **`hour`** (integer, required): Hour (0-23).
-   **`minute`** (integer, required): Minute (0-59).
-   **`second`** (integer, optional): Seconds (0-59, default: 0).
-   **`latitude`** (float, required): Latitude (-90 to 90).
-   **`longitude`** (float, required): Longitude (-180 to 180).
-   **`timezone`** (string, required): IANA timezone identifier.
-   **`using_default_location`** (boolean, optional): Metadata flag (default: false).
-   **`location_precision`** (integer, optional): Decimal places for coordinate rounding in the response (0-10, default: 0). Display rounding only.

#### Complete Request Example

```json
{
    "year": 1993,
    "month": 10,
    "day": 10,
    "hour": 12,
    "minute": 12,
    "latitude": 51.5074,
    "longitude": -0.1276,
    "timezone": "Europe/London",
    "location_precision": 4
}
```

### Response Body

-   **`status`** (string): `"OK"` on success.
-   **`context`** (string): AI-optimized XML context string describing the moon phase overview.
-   **`moon_phase_overview`** (object): Complete moon phase overview -- see [Moon Phase](../data/moon_phase.md) for the full field reference.

The `context` field is placed **before** `moon_phase_overview` in the response, consistent with other context endpoints.

#### Response Example (abbreviated)

```json
{
    "status": "OK",
    "context": "<moon_phase_overview timestamp=\"750251520\" datestamp=\"Sun, 10 Oct 1993 11:12:00 +0000\">...\n</moon_phase_overview>",
    "moon_phase_overview": {
        "timestamp": 750251520,
        "datestamp": "Sun, 10 Oct 1993 11:12:00 +0000",
        "moon": { "phase_name": "Waning Crescent", "illumination": "32%", "..." : "..." },
        "sun": { "sunrise_timestamp": "07:15", "sunset_timestamp": "18:18", "..." : "..." },
        "location": { "latitude": "51.5074", "longitude": "-0.1276", "precision": 4 }
    }
}
```

### Error Responses

Same as `/api/v5/moon-phase`. Returns `422 Unprocessable Entity` for missing required fields, invalid timezone, out-of-range values, or extra/unknown fields.
