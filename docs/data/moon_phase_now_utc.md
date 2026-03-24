---
title: 'Moon Phase Now (UTC)'
description: 'Get the current moon phase at Greenwich Observatory in real time. Instant lunar data with no required parameters for "Moon right now" features.'
order: 11
---

# Moon Phase Now (UTC) Endpoint

## `POST /api/v5/moon-phase/now-utc`

> **[View Complete Example](../examples/moon_phase_now_utc)**

This endpoint returns detailed moon phase information for the **current UTC moment** at Greenwich Observatory (51.4779°N, 0.0015°W). It is the moon phase equivalent of `/api/v5/now/subject`.

All times in the response (sunrise, sunset, etc.) are in **UTC** (`Etc/UTC` timezone).

**Important:** This endpoint uses strict validation. Only `using_default_location` and `location_precision` are accepted. Any other field (e.g., `year`, `latitude`, `timezone`, `city`) will be rejected with a `422` error.

### Use Cases

-   "Moon right now" widget in an app.
-   Real-time lunar phase display.
-   Quick check of current illumination and upcoming phases.

### Request Body

All fields are optional. An empty JSON object `{}` is a valid request.

-   **`using_default_location`** (boolean, optional): Metadata flag (default: `true`).
-   **`location_precision`** (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: `0`). This is display rounding only — calculations always use the full-precision Greenwich coordinates.

#### Complete Request Example

```json
{
    "using_default_location": true,
    "location_precision": 4
}
```

#### Minimal Request Example

```json
{}
```

### Response Body

Returns the same `MoonPhaseOverviewModel` structure as `/api/v5/moon-phase`, computed for the current UTC time at Greenwich.

-   **`status`** (string): `"OK"`.
-   **`moon_phase_overview`** (object): Complete moon phase overview — see [Moon Phase](moon_phase.md) for the full field reference.

Key differences from `/api/v5/moon-phase`:

-   Date/time is always the **current UTC moment** (not user-specified).
-   Location is always **Greenwich Observatory** (51.4779°N, 0.0015°W).
-   Timezone is always **`Etc/UTC`**.
-   `using_default_location` defaults to `true` (instead of `false`).

### Error Responses

This endpoint returns `422 Unprocessable Entity` if:

-   **Extra/unknown fields** are sent (e.g., `year`, `latitude`, `timezone`, `city`). Only `using_default_location` and `location_precision` are accepted.
-   **`location_precision`** is outside the valid range (0-10).
