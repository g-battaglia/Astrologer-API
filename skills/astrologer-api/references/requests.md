# Requests and examples

Contents: subject and location rules; paired charts; returns; current sky; Moon phases; Sun times; planetary hours; dominants.

## Subject and location

| Fields | Meaning |
| --- | --- |
| `year`, `month`, `day` | Required local calendar date; impossible dates are rejected. |
| `hour`, `minute` | Required local wall-clock time, 0–23 and 0–59. |
| `second` | Optional, defaults to 0. |
| `city` | Required, including when coordinates are supplied. |
| `name` | Optional display name, defaults to `Subject`. |
| `latitude`, `longitude`, `timezone` | Supply all three for deterministic coordinate-based calculation. |
| `nation` | Optional two-letter country code, such as `GB` or `IT`. |
| `geonames_username` | The caller's GeoNames account, for city lookup when coordinates are unavailable. |
| `is_dst` | Optional override for daylight-saving ambiguity; normally omit. |

The numeric time is local to `timezone`, not UTC unless that timezone is UTC. Use an IANA name such as `Europe/Rome`, not an offset string or `CET`. Do not pre-convert local birth time to UTC and then send it with the original local timezone.

Coordinates accept latitude −90 to 90 and longitude −180 to 180. Zero is a valid coordinate. Partial coordinates without a GeoNames username are rejected. Complete coordinates take precedence over a redundant GeoNames username; partial coordinates with GeoNames are discarded in favour of lookup. Prefer one explicit strategy in client code.

When time or location is missing, ask for it or explain the limitation. If the user explicitly chooses an estimated time, label it as estimated; houses and angles depend on it. For ambiguous daylight-saving times, resolve the ambiguity rather than choosing `is_dst` arbitrarily.

Years use astronomical numbering: 0 means 1 BCE, −1 means 2 BCE. The subject schema accepts −13200 through 9999; schema acceptance alone does not guarantee that every calculation, house system or historical timezone is meaningful over that whole span.

## Paired charts

### POST /api/v6/chart-data/synastry

```json
{
  "first_subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome"
  },
  "second_subject": {
    "name": "Ben", "year": 1992, "month": 9, "day": 12,
    "hour": 16, "minute": 30, "city": "London",
    "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"
  },
  "include_house_comparison": true,
  "include_relationship_score": true
}
```

Use `/chart/synastry` for an SVG and `/context/synastry` for XML. `/compatibility-score` accepts the same data request and returns the Ciro Discepolo score and rule breakdown. That score is not a percentage or a probability; keep its returned description alongside the value.

### POST /api/v6/chart/composite

```json
{
  "first_subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome"
  },
  "second_subject": {
    "name": "Ben", "year": 1992, "month": 9, "day": 12,
    "hour": 16, "minute": 30, "city": "London",
    "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"
  },
  "composite_type": "Midpoint",
  "house_anchor": "auto",
  "theme": "dark"
}
```

`composite_type` is `Midpoint` or `Davison`, with exact capitalization. `house_anchor` accepts `auto`, `ascendant` or `midheaven`; leave it at `auto` unless the user has a reason to override it. For data or context, remove `theme` and use `/chart-data/composite` or `/context/composite`.

### POST /api/v6/chart/transit

```json
{
  "first_subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome"
  },
  "transit_subject": {
    "name": "Transit", "year": 2026, "month": 10, "day": 1,
    "hour": 12, "minute": 0, "city": "London",
    "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"
  },
  "theme": "classic",
  "language": "EN"
}
```

The transit subject describes the target instant and observer location; it is not a second natal subject. In the returned dual-chart data it appears as `second_subject`. Remove rendering fields when using `/chart-data/transit` or `/context/transit`.

## Solar and lunar returns

### POST /api/v6/chart/solar-return

```json
{
  "subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome"
  },
  "iso_datetime": "2026-01-01T00:00:00+00:00",
  "return_location": {
    "city": "London", "latitude": 51.5074,
    "longitude": -0.1278, "timezone": "Europe/London"
  },
  "direction": "next",
  "wheel_type": "dual",
  "theme": "classic"
}
```

The natal subject stays unchanged. `return_location` changes the return chart's location. Omit it when no relocation is intended. Choose an explicit offset in `iso_datetime` so the starting instant is unambiguous.

Alternatively supply `year` and optional `month` and `day` instead of `iso_datetime`. A month requires a year; a non-default day requires both. These values locate the search start, not the exact return time. `direction` defaults to `next`; use `previous` to search backward. Starting from an exact return instant reported by the API requests the following or preceding return, with ordering at whole-second resolution.

`wheel_type: "dual"` compares natal and return; `single` displays the return alone. For a lunar return change the path to `/chart/lunar-return`. For data or XML, use the corresponding `/chart-data/…` or `/context/…` route and remove `theme`.

## Current sky

### POST /api/v6/now/chart

```json
{
  "name": "Current sky",
  "theme": "dark",
  "style": "modern"
}
```

Current-time routes do not accept a nested `subject` or an arbitrary observer location. They use current UTC at Greenwich. `/now/subject` and `/now/context` accept subject configuration such as `zodiac_type`, but not rendering options. `{}` is a valid minimal body; do not omit the body entirely. For another place or instant, use the ordinary subject/chart endpoint with explicit inputs.

## Moon phases

### POST /api/v6/moon-phase

```json
{
  "year": 2026, "month": 6, "day": 21,
  "hour": 12, "minute": 0,
  "latitude": 51.5074, "longitude": -0.1278,
  "timezone": "Europe/London",
  "location_precision": 4
}
```

These fields are flat: no subject, city, name or chart rendering options. `location_precision` controls rounding of returned coordinates. `/moon-phase/context` takes the same body and adds XML. `/moon-phase/now-utc` and `/moon-phase/now-utc/context` accept `{}` and optional presentation settings, not date/location overrides.

## Sun times and planetary hours

### POST /api/v6/sun/times

```json
{
  "year": 2026, "month": 6, "day": 21,
  "latitude": 51.5074, "longitude": -0.1278,
  "timezone": "Europe/London"
}
```

### POST /api/v6/sun/planetary-hours

```json
{
  "year": 2026, "month": 6, "day": 21,
  "hour": 11, "minute": 30,
  "latitude": 51.5074, "longitude": -0.1278,
  "timezone": "Europe/London"
}
```

Sun Times accepts a date, not a time. Planetary Hours also requires `hour`; `minute` defaults to 0. Before sunrise, the current planetary day can begin on the previous civil date. Planetary hours divide daylight and night into 12 parts each, so their durations are not necessarily 60 minutes. A location with no required sunrise/sunset can produce an error rather than a 24-entry table.

## Dominant planets

### POST /api/v6/analysis/dominants

```json
{
  "subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome"
  },
  "strategy": "modern",
  "include_score_breakdown": true
}
```

Strategies are `modern`, `almuten_figuris` and `elemental`. Rankings and available categories depend on the strategy; do not treat every strategy's results as interchangeable or assume every winner is non-null.
