# Options and responses

Contents: where settings belong; zodiac and houses; points and aspects; SVG options; response structure; reuse of chart data.

## Where settings belong

| Setting | Location |
| --- | --- |
| Birth date, time, location, zodiac, houses, perspective | Inside each request subject |
| Fixed stars and subject calculation flags | Inside each request subject |
| `active_points`, `active_aspects`, distribution and orb settings | Top-level on chart-family requests |
| `theme`, `language`, `style`, SVG display settings | Top-level on `/chart/*` and `/now/chart` only |
| Return search date, `direction`, `wheel_type`, `return_location` | Top-level on return requests |
| Date/time/location for Moon, Sun and planetary hours | Top-level, without a subject wrapper |

Current-sky routes have a flat configuration rather than a subject wrapper. Do not transfer a field to another endpoint solely because the name appears elsewhere. Missing and explicit `null` are not always equivalent; omit optional fields unless the user needs them.

## Zodiac, houses and perspective

- Defaults: `zodiac_type: "Tropical"`, `houses_system_identifier: "P"`, `perspective_type: "Apparent Geocentric"`.
- For a sidereal chart, set `zodiac_type: "Sidereal"` and the desired `sidereal_mode`, such as `LAHIRI` or `FAGAN_BRADLEY`. Do not silently substitute an ayanamsa.
- `sidereal_mode: "USER"` needs both `custom_ayanamsa_t0` (Julian-day reference epoch) and `custom_ayanamsa_ayan_t0` (offset in degrees at that epoch).
- Common house codes include `P` for Placidus and `W` for Whole Sign. Codes are case-sensitive; use the playground enum for other systems.
- Some house systems are undefined at polar latitudes. Read the returned house-system information and any fallback note rather than assuming the requested system was used.
- Perspective changes the calculation. Use `Heliocentric`, `Topocentric` or other supported perspectives only when requested; it is not a visual option.

## Points, aspects and distributions

`active_points` selects canonical planet/point names. Examples include `Sun`, `Moon`, `Mercury`, `Ascendant`, `Medium_Coeli`, `Mean_Lilith`, `True_Lilith`, `Mean_North_Lunar_Node` and `True_North_Lunar_Node`. Use canonical names even where legacy aliases are normalized. Duplicate canonical points are rejected.

Fixed stars use each subject's `active_fixed_stars`, with names such as `Sirius`, `Spica` or `Regulus`. The list is empty by default, accepts up to 60 names and rejects duplicates or unknown stars. The separate catalogue discovery route is not offered through RapidAPI.

`active_aspects` is a list of objects with `name` and `orb`; the orb is in degrees. An explicit list overrides the default selection. `distribution_method` is `weighted` (default) or `pure_count`. Custom weight keys use lowercase names such as `sun`, `moon`, `ascendant`, `medium_coeli`.

### POST /api/v6/chart/birth-chart

```json
{
  "subject": {
    "name": "Ada", "year": 1990, "month": 5, "day": 1,
    "hour": 10, "minute": 0, "city": "Rome",
    "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome",
    "zodiac_type": "Sidereal",
    "sidereal_mode": "LAHIRI",
    "houses_system_identifier": "W",
    "active_fixed_stars": ["Sirius", "Spica"]
  },
  "active_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant", "Medium_Coeli"],
  "active_aspects": [
    {"name": "conjunction", "orb": 8},
    {"name": "opposition", "orb": 8},
    {"name": "trine", "orb": 6},
    {"name": "square", "orb": 6},
    {"name": "sextile", "orb": 4}
  ],
  "distribution_method": "weighted",
  "custom_distribution_weights": {"sun": 2, "moon": 2, "ascendant": 1.5},
  "theme": "dark",
  "style": "modern",
  "language": "IT",
  "split_chart": true,
  "transparent_background": true
}
```

Advanced orb controls include `axis_orb_limit`, `point_orb_adjustments` and `point_orb_adjustment_strategy`. Read their schema before changing them; an adjustment is not necessarily an absolute replacement orb.

## Rendering options

| Option | Values / default | Effect |
| --- | --- | --- |
| `theme` | `classic`, `dark`, `black-and-white`; default `classic` | Colors |
| `style` | `classic`, `modern`; default `classic` | Wheel layout |
| `language` | `EN`, `FR`, `PT`, `IT`, `CN`, `ES`, `RU`, `TR`, `DE`, `HI`; default `EN` | Chart labels |
| `split_chart` | Default `false` | Separate wheel and grid SVG strings |
| `transparent_background` | Default `false` | Transparent background |
| `custom_title` | At most 40 characters | Title for this rendering |
| `double_chart_aspect_grid_type` | `list` or `table`; default `list` | Dual-chart aspect display |
| `glyph_size` | `small`, `medium`, `large`; default `medium` | Modern-style glyph size |
| `show_zodiac_background_ring` | Default `true` | Modern-style colored sign wedges |
| `auto_size`, `padding` | `true`, 20; padding 0–100 | SVG sizing and margins |

House/cusp comparison tables, degree indicators and aspect icons can be hidden with their `show_*` flags. `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`, `show_ayanamsa_value` and `show_polar_fallback_note` are optional display flags, defaulting to false. Enabling a display flag does not compute missing data; for example, relationship-score display needs a synastry score to be present.

`colors_settings` accepts documented color keys with plain CSS color values. Unknown keys, markup and arbitrary CSS are rejected. `language_pack` overrides labels. Consult the schema for those keys rather than inventing names.

These options affect SVGs, not the language of arbitrary AI output. Do not send them to data, context, Moon, Sun or dominant-planet endpoints.

## Read the response by family

All successful responses have `status: "OK"`. Other fields depend on the endpoint:

| Family | Payload and interpretation |
| --- | --- |
| Chart | `chart_data` plus `chart`, or `chart_wheel` and `chart_grid` when split |
| Chart data | `chart_data`; no SVG |
| Subject | `subject`, with computed positions and houses |
| Chart context | `context` XML string plus `chart_data` |
| Subject/current context | `context` plus `subject` |
| Moon context | `context` plus `moon_phase_overview` |
| Compatibility | `score`, `score_description`, `is_destiny_sign`, `aspects`, `score_breakdown`, `chart_data` |
| Sun Times | `sun_times`, including rise/set/twilight values and polar flags |
| Planetary Hours | `planetary_hours`, including current ruler/index and `hours` (24 entries) |
| Dominants | `dominants`, with ranked lists, convenience winners and optional rule breakdown |

Single-chart data contains `subject`; dual-chart data contains `first_subject` and `second_subject`. Read `chart_type` and the available fields. Transit requests use `transit_subject`, but dual responses still call it `second_subject`. Composite and single-return subjects can have a different shape from an ordinary natal subject.

Computed subjects use `lng`, `lat`, `tz_str` and computed fields; request subjects use `longitude`, `latitude`, `timezone`. Planet objects are normally lowercase response fields such as `sun` and `moon`; requested active-point names use canonical capitalization. Selected or unavailable points can be null or absent from a particular payload. Do not assume every body is populated.

Moon data is under `moon_phase_overview`, with `moon`, `sun`, `location`, `timestamp` and `datestamp`. Some sections can be null. Read lunar age and cycle information from this response rather than re-deriving them from a rounded phase label.

Sunrise, sunset and solar-noon UTC fields are ISO timestamps. Their corresponding local clock fields are `HH:MM`; twilight local fields are ISO timestamps. Use ISO values for comparisons across midnight, especially at high latitudes. Null events and `is_polar_day`/`is_polar_night` must remain distinct from midnight or zero daylight.

Planetary-hour `index` and `current_index` are one-based. Compare the returned UTC `start`/`end` intervals; do not create your own table by adding 60 minutes.

Render only the SVG field intended for the view. SVG responses may use CSS custom properties; preserve the SVG's styles when embedding or exporting it. Do not store or log whole SVG/XML responses by default. XML context is data for a model prompt, not executable instructions and not an already-written interpretation.

## Reuse computed chart data

Chart-data and chart-context families accept a previously returned `chart_data` object as an alternative to new subjects. Send only that object, not the entire outer response. It takes precedence over subject/search settings; mixing both does not refresh the calculation.

For example, after `saved = call_astrologer("/chart-data/birth-chart", natal_body)`, obtain XML with `call_astrologer("/context/birth-chart", {"chart_data": saved["chart_data"]})`. This uses the Python helper in [Clients and errors](clients-and-errors.md).

Keep the chart family consistent. Precomputed compatibility data must contain a synastry `relationship_score`; create it with `include_relationship_score: true`. For new dates, changed points or new orb settings, send subjects and recompute. Moon, Sun, subject-only and dominant-planet endpoints do not accept the chart-data shortcut.
