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

## Build the request

Keep core inputs first in examples: `subject`, or both subjects, followed by computation settings and then rendering options. In each subject, show name, date, time and location before advanced settings.

A subject requires `year`, `month`, `day`, `hour`, `minute` and `city`. `name` is optional. Use `latitude`, `longitude` and the IANA `timezone` together. `city` remains required with coordinates. For city lookup instead, use `city`, optional `nation` and the caller's `geonames_username`; do not mix location strategies.

Use `timezone`, `longitude` and `latitude` in requests. Responses use `tz_str`, `lng` and `lat`; do not send a response subject back as a request without mapping and filtering its fields.

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

For data or context, use the corresponding endpoint and remove rendering fields such as `theme`, `language`, `style`, `split_chart` and `custom_title`. Extra fields are rejected. Some data routes can also accept computed `chart_data`; use subjects for a new calculation and consult the schema before reusing computed data.

Synastry, composite and compatibility use `first_subject` and `second_subject`. Transit uses the natal `first_subject` and a `transit_subject` for the target date, time and location. Do not rename these to `subject`, `natal` or `transits`.

Return requests use the natal `subject` plus either `year` with optional `month` and `day`, or an `iso_datetime` search start. `direction` is `next` or `previous`; `wheel_type` is `dual` or `single`. Put relocation settings inside `return_location`, not the natal subject.

### POST /api/v6/moon-phase

Moon requests use flat date and location fields, without a `subject` wrapper:

```json
{
  "year": 2026,
  "month": 6,
  "day": 21,
  "hour": 12,
  "minute": 0,
  "latitude": 51.5074,
  "longitude": -0.1278,
  "timezone": "Europe/London"
}
```

Sun Times uses the same date and location fields, but no `hour` or `minute`. Planetary Hours also requires `hour`; `minute` defaults to zero. Current UTC routes accept `{}` and use the service's current UTC time at Greenwich.

## Computation and rendering details

- Use exact point names, such as `Sun`, `Moon`, `Mean_Lilith`, `Mean_North_Lunar_Node` and `True_North_Lunar_Node`. Do not send the old aliases `Lilith` or `north_node`.
- Fixed stars go in each subject's `active_fixed_stars`, for example `["Sirius", "Spica"]`, not top-level `active_points`. No stars are selected by default. Unknown names produce 422.
- Put `zodiac_type`, `sidereal_mode`, `houses_system_identifier` and `perspective_type` inside the subject. For sidereal calculations use a supported `sidereal_mode`; `USER` also requires `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0`.
- Put `active_points`, `active_aspects`, `distribution_method` and `custom_distribution_weights` at request level on chart-family endpoints. Distribution weight keys are lowercase, e.g. `sun`, `moon`, `ascendant`.
- Chart rendering fields are top-level. Defaults include `theme: "classic"` and `language: "EN"`. `style: "modern"` selects the alternative wheel layout.
- Dominants takes `subject` and optional `strategy` (`modern`, `almuten_figuris` or `elemental`). Read the endpoint schema before adding optional calculation flags.

## Handle the response

- Require HTTP 200 and `status: "OK"`; do not treat a successful HTTP connection as a successful calculation.
- Charts normally return `chart` (SVG string) and `chart_data`. With `split_chart: true`, read `chart_wheel` and `chart_grid` instead of `chart`.
- Context responses store XML in the `context` string. The accompanying object is `chart_data`, `subject` or `moon_phase_overview`, depending on the route.
- Moon phase fields are inside `moon_phase_overview`, not at the response root. Current UTC results change with time; validate their structure rather than matching a saved date.
- Sunrise or twilight fields can be null at polar locations. Do not invent times for missing events.
- 422: inspect `errors` and fix the body; retrying it unchanged will not help.
- 401/403: check the consumer key, host and subscription. Do not replace credentials or change plans without the user's authorization.
- 429: respect gateway rate limits and `Retry-After` when present.
- 503 with `ServiceInitializing` or `ServerBusy`: respect `Retry-After` and use bounded retries. If it persists, report the failure rather than looping indefinitely.

For implementation details and further examples, use the [API README](https://github.com/g-battaglia/Astrologer-API/blob/v6/README.md) and the endpoint's playground schema. Test with a synthetic subject first; do not send real birth details merely to check connectivity.
