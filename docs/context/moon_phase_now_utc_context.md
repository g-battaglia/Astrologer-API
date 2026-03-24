---
title: 'Moon Phase Now Context (UTC)'
description: 'Get the current moon phase at Greenwich with AI-optimized XML context for LLM integration. Instant lunar data with AI context.'
order: 10
---

# Moon Phase Now (UTC) Context Endpoint

## `POST /api/v5/moon-phase/now-utc/context`

> **[View Complete Example](../examples/moon_phase_now_utc_context)**

Returns detailed moon phase information for the **current UTC moment** at Greenwich Observatory (51.4779N, 0.0015W) with an AI-optimized XML context string. This is the context variant of `/api/v5/moon-phase/now-utc`.

All times in the response (sunrise, sunset, etc.) are in **UTC** (`Etc/UTC` timezone).

**Important:** This endpoint uses strict validation. Only `using_default_location` and `location_precision` are accepted. Any other field will be rejected with a `422` error.

### Use Cases

-   AI-powered "moon right now" features with LLM interpretation.
-   Real-time lunar context for AI chatbots.
-   Quick current moon phase data with AI-ready context.

### Request Body

All fields are optional. An empty JSON object `{}` is a valid request.

-   **`using_default_location`** (boolean, optional): Metadata flag (default: `true`).
-   **`location_precision`** (integer, optional): Decimal places for coordinate rounding (0-10, default: `0`). Display rounding only.

#### Minimal Request Example

```json
{}
```

### Response Body

-   **`status`** (string): `"OK"` on success.
-   **`context`** (string): AI-optimized XML context string describing the current moon phase overview.
-   **`moon_phase_overview`** (object): Complete moon phase overview -- see [Moon Phase](../data/moon_phase.md) for the full field reference.

Key differences from `/api/v5/moon-phase/context`:

-   Date/time is always the **current UTC moment** (not user-specified).
-   Location is always **Greenwich Observatory** (51.4779N, 0.0015W).
-   Timezone is always **`Etc/UTC`**.
-   `using_default_location` defaults to `true` (instead of `false`).

### Error Responses

Returns `422 Unprocessable Entity` if extra/unknown fields are sent or `location_precision` is outside 0-10.
