---
name: astrologer-api
description: Integrate the hosted Astrologer API through RapidAPI for SVG charts, astrology data, Moon phases, planetary hours and XML context. Use when writing or debugging clients for this service.
---

# Astrologer API

Use this skill for the public RapidAPI catalogue. It covers the 31 endpoints below, not every capability in the source repository. Follow the user's requested feature and language; do not add unrelated calculations or infrastructure.

## Connection

- Base URL: `https://astrologer.p.rapidapi.com/api/v6`
- All listed endpoints use `POST` with a JSON body, including current-time endpoints.
- Headers: `X-RapidAPI-Key`, `X-RapidAPI-Host: astrologer.p.rapidapi.com`, and `Content-Type: application/json`.
- Read the consumer key from the caller's environment or existing secret store. Keep it on the application's server; never embed it in browser code, examples or logs.
- The consumer key is not the provider's proxy secret. A client only needs the consumer key.
- Obtain a key through the [subscription page](https://www.kerykeion.net/astrologer-api/subscribe). Account changes and purchases remain the user's decision.

The [playground](https://rapidapi.com/gbattaglia/api/astrologer/playground/) provides schemas and examples. For these routes select version 6.0.0. Older guides using `/api/v5` describe a different contract; do not copy their field aliases into new requests.

## Select an endpoint

Paths below are relative to the base URL. Choose data when no image is needed, charts when an SVG is needed, and context when the consumer needs XML for a model prompt. Context endpoints return structured input, not generated predictions or prose.

| Group | Path | Main input | Result |
| --- | --- | --- | --- |
| Charts | `/chart/birth-chart` | `subject` | SVG + chart data |
| Charts | `/chart/transit` | `first_subject`, `transit_subject` | SVG + chart data |
| Charts | `/chart/synastry` | `first_subject`, `second_subject` | SVG + chart data |
| Charts | `/chart/composite` | `first_subject`, `second_subject` | SVG + chart data |
| Charts | `/chart/solar-return` | `subject`, return search start | SVG + chart data |
| Charts | `/chart/lunar-return` | `subject`, return search start | SVG + chart data |
| Charts | `/now/chart` | Options or `{}` | Current UTC sky SVG + data |
| Chart Data | `/chart-data/birth-chart` | `subject` | `chart_data` |
| Chart Data | `/chart-data/transit` | `first_subject`, `transit_subject` | `chart_data` |
| Chart Data | `/chart-data/synastry` | `first_subject`, `second_subject` | `chart_data` |
| Chart Data | `/chart-data/composite` | `first_subject`, `second_subject` | `chart_data` |
| Chart Data | `/compatibility-score` | `first_subject`, `second_subject` | Score, aspects, breakdown + data |
| Chart Data | `/chart-data/solar-return` | `subject`, return search start | `chart_data` |
| Chart Data | `/chart-data/lunar-return` | `subject`, return search start | `chart_data` |
| Chart Data | `/subject` | `subject` | `subject` |
| Chart Data | `/now/subject` | Options or `{}` | Current UTC `subject` |
| Moon Phase | `/moon-phase` | Date, time, coordinates, timezone | `moon_phase_overview` |
| Moon Phase | `/moon-phase/now-utc` | Options or `{}` | Current `moon_phase_overview` |
| Moon Phase | `/moon-phase/context` | Date, time, coordinates, timezone | XML + `moon_phase_overview` |
| Moon Phase | `/moon-phase/now-utc/context` | Options or `{}` | XML + current Moon data |
| AI Context | `/context/birth-chart` | `subject` | XML + `chart_data` |
| AI Context | `/context/transit` | `first_subject`, `transit_subject` | XML + `chart_data` |
| AI Context | `/context/synastry` | `first_subject`, `second_subject` | XML + `chart_data` |
| AI Context | `/context/composite` | `first_subject`, `second_subject` | XML + `chart_data` |
| AI Context | `/context/lunar-return` | `subject`, return search start | XML + return data |
| AI Context | `/context/solar-return` | `subject`, return search start | XML + return data |
| AI Context | `/now/context` | Options or `{}` | XML + current `subject` |
| AI Context | `/context/subject` | `subject` | XML + `subject` |
| Sun & Planetary Hours | `/sun/times` | Date, coordinates, timezone | `sun_times` |
| Sun & Planetary Hours | `/sun/planetary-hours` | Date, time, coordinates, timezone | `planetary_hours` |
| Dominants | `/analysis/dominants` | `subject` | `dominants` |

Event searches, batch operations, MCP, fixed-star catalogue lookup and operational probes are not in this RapidAPI catalogue. Do not suggest those routes as available here.

## Choose the relevant reference

- [Requests and examples](references/requests.md): subject fields, time zones, paired charts, returns, Moon and Sun requests, current-time calls, and dominant planets.
- [Options and responses](references/options-and-responses.md): zodiac and house settings, points and aspects, SVG customization, response field locations, and reuse of computed data.
- [Clients and errors](references/clients-and-errors.md): server-side Python and JavaScript clients, timeout and retry decisions, and checks before shipping an integration.

Read the relevant sections for the requested feature. The examples are complete JSON bodies for their named endpoints; they use synthetic subjects.

## Start with a small request

Keep `subject` (or both subjects) first in examples, then computation settings, then rendering options. Inside a subject show name, date, time and location before advanced settings.

### POST /api/v6/chart/birth-chart

```json
{
  "subject": {
    "name": "Ada",
    "year": 1990,
    "month": 5,
    "day": 1,
    "hour": 10,
    "minute": 0,
    "city": "Rome",
    "latitude": 41.9028,
    "longitude": 12.4964,
    "timezone": "Europe/Rome"
  },
  "theme": "classic"
}
```

For `/chart-data/birth-chart` or `/context/birth-chart`, use the same subject and remove `theme`. The first returns `chart_data`; the second also returns an XML `context` string.

## Contract essentials

- A subject requires `year`, `month`, `day`, `hour`, `minute` and `city`; `name` is optional. Use complete coordinates plus an IANA timezone, or GeoNames lookup. Do not invent an unknown birth time or location.
- Synastry, composite and compatibility use `first_subject` and `second_subject`. Transit uses `first_subject` and `transit_subject`. Moon and Sun endpoints use flat date/location fields.
- Requests use `timezone`, `longitude`, `latitude`; computed subjects use `tz_str`, `lng`, `lat`. Response objects are not valid request subjects without mapping and filtering.
- Computation options belong at request level on chart-family endpoints; zodiac, house and fixed-star settings belong inside each subject. Rendering options belong only on chart endpoints. Extra fields are rejected.
- Use canonical point names such as `Mean_Lilith` and `Mean_North_Lunar_Node`. Keep fixed stars in `subject.active_fixed_stars`, not `active_points`.
- Choose new subjects or precomputed `chart_data` deliberately. Where supported, `chart_data` takes precedence and calculation options do not recompute it.
- Require HTTP 200 and `status: "OK"`, then check the payload needed by the feature: SVG, chart data, XML, Moon data, Sun times or dominants. Do not mistake an empty successful response for a working integration.
- Handle 422 by fixing the body, 401/403 by checking credentials and subscription, and 429/503 with bounded retries that respect `Retry-After`. Do not silently change plans or loop indefinitely.

Use the [API README](https://github.com/g-battaglia/Astrologer-API/blob/v6/README.md) and the endpoint's playground schema for additional fields. Test connectivity with a synthetic subject before sending real birth details.
