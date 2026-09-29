"""MCP resource definitions for the Astrologer API v6.

Provides 13 resources registered via ``register_resources(mcp)``.
Each resource returns a Markdown string consumed by LLM clients
through the Model Context Protocol.
"""

from typing import get_args

from kerykeion.schemas import (
    AspectName,
    KerykeionChartLanguage,
    KerykeionChartTheme,
    KerykeionGlyphSize,
)

# Render option lists from the kerykeion literals so the docs cannot drift from
# the installed library (audit L-group E).
_THEME_OPTIONS = ", ".join(f'"{value}"' for value in get_args(KerykeionChartTheme))
_LANGUAGE_OPTIONS = ", ".join(get_args(KerykeionChartLanguage))
_ASPECT_NAMES = ", ".join(get_args(AspectName))
_GLYPH_SIZE_OPTIONS = ", ".join(f'"{value}"' for value in get_args(KerykeionGlyphSize))


def register_resources(mcp):
    # ------------------------------------------------------------------
    # 1. API Overview
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/overview")
    def api_overview() -> str:
        return """\
# Astrologer API v6 Overview

## What It Does
The Astrologer API exposes the full power of **kerykeion v6** over HTTP (REST)
and MCP (Model Context Protocol).  It calculates birth charts, synastry,
composite charts, transits, solar/lunar returns, moon phases, and a wide range
of advanced astronomical and astrological features.

## Core Capabilities
- **Birth chart** (natal): planetary positions, houses, aspects, element/quality distribution
- **Synastry**: bi-wheel comparison between two charts
- **Composite chart**: Midpoint and Davison methods
- **Transit chart**: current sky overlaid on a natal chart
- **Solar return / Lunar return**: annual and monthly return charts
- **Heliocentric return**: planetary return in heliocentric perspective
- **Lunar node crossing**: nodal return chart
- **Moon phase**: detailed lunar phase data with illumination, upcoming phases, and eclipses

## Advanced Features (v6)
- Eclipse search (solar & lunar, global or local)
- Planetary phenomena (phase angle, elongation, magnitude, morning/evening star)
- Planetary nodes (ascending/descending, perihelion/aphelion)
- Heliacal events (first/last visibility of planets and stars)
- Occultations (lunar occultations of the planets)
- Relocated chart (same planets, new location)
- Fixed star discovery (prominent stars conjunct chart points)
- Primary directions (Placidus semi-arc, Ptolemy/Naibod rate keys)
- Astro-cartography (ACG planetary lines on Earth's surface)
- Declination aspects (parallel / contra-parallel, single or dual chart)
- Transit events (time-range analysis with exact-moment refinement)
- Transit moments (day-by-day aspect snapshots)
- Ephemeris generation (positions over a date range at configurable intervals)
- Report generation (human-readable text report)
- Lunations, retrograde stations, sign ingresses (event search over a date range)
- Midpoints (full midpoint table for a chart)
- Time-lord techniques: zodiacal releasing, annual profections, firdaria
- Horary indicators (significators + considerations before judgment)
- Secondary progressions and solar arc directions (data)
- Transit batch (many transit snapshots over a date range in one call)
- Dominants (planet, sign, element, modality, house)
- Void-of-course Moon, sun times, planetary hours

Not exposed via MCP (REST only): `/calendar`,
`/events/mundane-aspects`, `/moon/void-of-course/windows`,
`GET /fixed-stars/catalog`, the `/context/*` variants of
secondary-progressions / solar-arc-directions / midpoints /
primary-directions, and the SVG charts of secondary progressions and
solar arc directions.

## v6 Calculation Options
Each subject can enable optional calculations:
- `calculate_dignities` -- essential dignities, Chaldean decans, Egyptian terms
- `calculate_nakshatra` -- Vedic lunar mansions, pada, Vimsottari Dasha lord
- `nakshatra_ayanamsa` -- the ayanamsa those mansions are read through on a
  non-sidereal chart (default "LAHIRI"; null for the uncorrected legacy values)
- `calculate_gauquelin` -- Gauquelin sector position (1-36)
- `calculate_nutation` -- nutation and obliquity parameters
- `calculate_local_space` -- azimuth and altitude from observer's location
- `active_fixed_stars` -- list of fixed stars to compute from the libephemeris catalog (no automatic defaults)

## Perspective Types
11 astronomical perspectives: Apparent Geocentric, Heliocentric, Topocentric,
True Geocentric, Selenocentric, Mercurycentric, Venuscentric, Marscentric,
Jupitercentric, Saturncentric, Barycentric.

## Three Output Modes
1. **Data-only** (`/chart-data/*`) -- JSON with positions, aspects, distributions
2. **SVG** (`/chart/*`) -- JSON data plus rendered SVG chart
3. **AI context** (`/context/*` or `include_ai_context` flag) -- XML-structured
   context string optimized for LLM consumption

## Best Practices for AI Applications
- Use the `/context` endpoints or `include_ai_context=true` to get pre-formatted
  analysis-ready data.
- Request only the points and aspects you need via `active_points` / `active_aspects`.
- Use `axis_orb_limit` to tighten orbs for angular points (ASC/MC/DSC/IC).
- For transit analysis over a period, prefer `get_transit_events` (grouped events)
  or `get_transit_moments` (daily snapshots) over repeated single-transit calls.
- Enable `calculate_dignities` for traditional astrology depth.
"""

    # ------------------------------------------------------------------
    # 2. Subject Model Reference
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/subject-model")
    def subject_model_reference() -> str:
        return """\
# Subject Model Reference

A **subject** represents a person, event, or moment in time/space for which
astrological calculations are performed.

## Required Fields
| Field   | Type  | Description |
|---------|-------|-------------|
| name    | str   | Display name for the subject |
| year    | int   | Year (-13200 to 9999, astronomical numbering: 0 = 1 BCE) |
| month   | int   | Month (1-12) |
| day     | int   | Day (1-31) |
| hour    | int   | Hour (0-23) |
| minute  | int   | Minute (0-59) |
| city    | str   | City name |

## Location (provide one set)
**Option A -- coordinates:**
| Field     | Type  | Description |
|-----------|-------|-------------|
| latitude  | float | -90 to 90 |
| longitude | float | -180 to 180 |
| timezone  | str   | IANA timezone (e.g. "Europe/Rome") |

**Option B -- GeoNames lookup:**
| Field              | Type | Description |
|--------------------|------|-------------|
| geonames_username  | str  | GeoNames API username for automatic geocoding |

## Optional Fields
| Field                    | Type        | Default            | Description |
|--------------------------|-------------|--------------------|-------------|
| second                   | int         | 0                  | Seconds (0-59) |
| altitude                 | float       | null               | Altitude above sea level in meters |
| is_dst                   | bool        | null               | Override automatic DST detection |
| nation                   | str         | "GB"               | ISO 3166-1 alpha-2 country code (the MCP tools default it to "GB" when omitted) |
| zodiac_type              | str         | "Tropical"         | "Tropical" or "Sidereal" |
| sidereal_mode            | str         | null               | Ayanamsha (required when zodiac_type="Sidereal") |
| perspective_type         | str         | "Apparent Geocentric" | Astronomical perspective |
| houses_system_identifier | str         | "P" (Placidus)     | House system identifier |
| custom_ayanamsa_t0       | float       | null               | Reference epoch (Julian Day) for USER sidereal mode |
| custom_ayanamsa_ayan_t0  | float       | null               | Ayanamsa offset in degrees for USER sidereal mode |

## v6 Calculation Flags
| Field                   | Type       | Default | Description |
|-------------------------|------------|---------|-------------|
| calculate_dignities     | bool       | false   | Essential dignities, Chaldean decans, Egyptian terms |
| calculate_nakshatra     | bool       | false   | Vedic Nakshatra, pada, Vimsottari Dasha lord |
| nakshatra_ayanamsa      | str        | "LAHIRI" | Ayanamsa that rotates a non-sidereal chart onto the nakshatra grid; null for the uncorrected legacy reading. Ignored (and echoed as null) when the chart is already Sidereal |
| calculate_gauquelin     | bool       | false   | Gauquelin sector position (1-36) |
| calculate_nutation      | bool       | false   | Nutation and obliquity parameters |
| calculate_local_space   | bool       | false   | Azimuth and altitude from observer location |
| active_fixed_stars      | list[str]  | null    | Fixed star names to compute (libephemeris catalog, no defaults) |
| active_midpoints        | list[str]  | null    | Midpoint pair identifiers to materialize on the wheel (e.g. "Sun_Moon"; max 100) |

## Example JSON
```json
{
  "name": "John Doe",
  "year": 1990, "month": 6, "day": 15,
  "hour": 14, "minute": 30, "second": 0,
  "city": "Rome", "nation": "IT",
  "latitude": 41.9028, "longitude": 12.4964, "timezone": "Europe/Rome",
  "zodiac_type": "Tropical",
  "perspective_type": "Apparent Geocentric",
  "houses_system_identifier": "P",
  "calculate_dignities": true,
  "calculate_nakshatra": true,
  "nakshatra_ayanamsa": "LAHIRI"
}
```
"""

    # ------------------------------------------------------------------
    # 3. Chart Configuration
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/chart-config")
    def chart_config() -> str:
        return (
            """\
# Chart Configuration

Chart rendering options control the visual output of SVG charts.
These are passed alongside the subject in chart endpoints (`/chart/*`).

## Theme & Language
| Field     | Type | Default   | Options |
|-----------|------|-----------|---------|
| theme     | str  | "classic" | __THEME_OPTIONS__ |
| language  | str  | "EN"      | __LANGUAGE_OPTIONS__ |

## Chart Style (v6)
| Field                          | Type | Default   | Description |
|--------------------------------|------|-----------|-------------|
| style                          | str  | "classic" | "classic" (traditional wheel) or "modern" (concentric rings) |
| glyph_size                     | str  | "medium"  | Size of the planet cluster on the wheel: __GLYPH_SIZE_OPTIONS__ ("large" is the planet glyph at the classic style's own size, in the default configuration — zodiac background ring active). Modern style only |
| show_zodiac_background_ring    | bool | true      | Show colored zodiac wedges (modern style only) |
| double_chart_aspect_grid_type  | str  | "list"    | "list" (vertical) or "table" (grid matrix) for dual charts |

## Sizing & Layout (v6)
| Field    | Type | Default | Description |
|----------|------|---------|-------------|
| auto_size | bool | true   | Automatically size SVG to fit content |
| padding   | int  | 20     | Padding around chart in pixels (0-100) |

## Display Toggles
| Field                           | Type | Default | Description |
|---------------------------------|------|---------|-------------|
| split_chart                     | bool | false   | Return wheel and aspect grid as separate SVGs |
| transparent_background          | bool | false   | Transparent background instead of theme default |
| show_house_position_comparison  | bool | true    | House comparison table on the wheel |
| show_cusp_position_comparison   | bool | true    | Cusp comparison table (dual charts) |
| show_degree_indicators          | bool | true    | Radial lines and degree numbers |
| show_aspect_icons               | bool | true    | Aspect icons on aspect lines |
| show_diurnality                 | bool | true    | Print "Diurnality: Diurnal/Nocturnal" (Sun above or below the horizon) in the info panel. |
| show_motion_state               | bool | false   | Label stationary planets on the wheel: "SR" (turning retrograde) or "SD" (turning direct) |
| show_out_of_bounds              | bool | false   | Badge points past the Sun's declination extremes (~±23°26') with "OOB" in the point tables |
| show_aspect_movement            | bool | false   | Dash the aspect lines of separating aspects; applying aspects stay solid |
| show_relationship_score         | bool | false   | Print the synastry relationship score in the info panel (needs include_relationship_score) |
| show_ayanamsa_value             | bool | false   | Append the ayanamsa offset in degrees to the zodiac line (sidereal charts only) |
| show_polar_fallback_note        | bool | false   | Mark the house-system line when a polar latitude forced a substitute system |
| custom_title                    | str  | null    | Override chart title (max 40 chars) |

## Color & Label Overrides (v6)
| Field          | Type       | Default | Description |
|----------------|------------|---------|-------------|
| colors_settings | dict[str,str] | null | Known chart-key CSS color overrides; plain colors only (e.g. `{"zodiac_bg_1":"#FF0000"}`) |
| language_pack   | dict[str,str] | null | Custom label translations |

## Data Configuration (also available on data-only endpoints)
| Field                         | Type       | Default    | Description |
|-------------------------------|------------|------------|-------------|
| active_points                 | list[str]  | all defaults | Override active points |
| active_aspects                | list       | all defaults | Override active aspects with custom orbs. Each item: `{"name": "<aspect>", "orb": <degrees>}`, e.g. `[{"name": "conjunction", "orb": 10}, {"name": "opposition", "orb": 8}]`. Valid names: __ASPECT_NAMES__. |
| distribution_method           | str        | "weighted" | "weighted" or "pure_count" |
| custom_distribution_weights   | dict       | null       | Custom weights for weighted distribution |
| axis_orb_limit                | float      | null       | Max orb override for axial points (ASC/MC/DSC/IC) |
""".replace("__THEME_OPTIONS__", _THEME_OPTIONS)
            .replace("__LANGUAGE_OPTIONS__", _LANGUAGE_OPTIONS)
            .replace("__ASPECT_NAMES__", _ASPECT_NAMES)
            .replace("__GLYPH_SIZE_OPTIONS__", _GLYPH_SIZE_OPTIONS)
        )

    # ------------------------------------------------------------------
    # 4. Zodiac Types & House Systems
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/reference/zodiac-houses")
    def zodiac_houses_reference() -> str:
        return """\
# Zodiac Types & House Systems

## Zodiac Types
- **Tropical** (default): based on the vernal equinox.
- **Sidereal**: fixed-star-based, requires a `sidereal_mode`.

## Sidereal Modes (48 available)
The API supports all 48 ayanamshas (sidereal modes).  Most commonly used:

| Mode              | Description |
|-------------------|-------------|
| LAHIRI            | Indian government standard (Chitrapaksha) |
| FAGAN_BRADLEY     | Western sidereal standard |
| RAMAN             | B.V. Raman's ayanamsha |
| KRISHNAMURTI      | KP (Krishnamurti Paddhati) |
| DELUCE            | Robert DeLuce |
| YUKTESHWAR        | Sri Yukteshwar |
| DJWHAL_KHUL       | Esoteric/Theosophical |
| TRUE_CITRA        | True Chitra ayanamsha |
| TRUE_REVATI       | True Revati ayanamsha |
| J2000             | Reference to J2000 epoch |
| USER              | Custom ayanamsha (set custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0) |

## Perspective Types (11)
| Perspective            | Description |
|------------------------|-------------|
| Apparent Geocentric    | Standard astrological perspective (default) |
| True Geocentric        | Geometric (light-time uncorrected) geocentric |
| Topocentric            | Observer-surface-adjusted geocentric |
| Heliocentric           | Sun-centered |
| Selenocentric          | Moon-centered |
| Mercurycentric         | Mercury-centered |
| Venuscentric           | Venus-centered |
| Marscentric            | Mars-centered |
| Jupitercentric         | Jupiter-centered |
| Saturncentric          | Saturn-centered |
| Barycentric            | Solar system barycenter |

## Composite Chart Types
| Type      | Description |
|-----------|-------------|
| Midpoint  | Midpoints of two charts' planetary positions (default) |
| Davison   | Chart cast for the space-time midpoint of both subjects |

## House Systems (23 available)
| ID | Name |
|----|------|
| P  | Placidus (default) |
| K  | Koch |
| O  | Porphyrius |
| R  | Regiomontanus |
| C  | Campanus |
| A  | Equal (Ascendant) |
| V  | Vehlow Equal |
| W  | Whole Sign |
| X  | Axial Rotation / Meridian |
| H  | Azimuthal / Horizontal |
| T  | Polich/Page (Topocentric) |
| B  | Alcabitius |
| M  | Morinus |
| U  | Krusinski-Pisa |
| Y  | APC Houses |
| D  | Equal (MC) |
| F  | Carter Poli-Equatorial |
| I  | Sunshine |
| i  | Sunshine alternative |
| L  | Pullen SD |
| N  | Equal / 1=Aries |
| Q  | Pullen SR |
| S  | Sripati |
"""

    # ------------------------------------------------------------------
    # 5. Astrological Points
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/reference/astrological-points")
    def astrological_points_reference() -> str:
        return """\
# Astrological Points Reference

## Classical Planets
Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn

## Modern Planets
Uranus, Neptune, Pluto

## Centaurs & TNOs
Chiron, Pholus, Ceres, Pallas, Juno, Vesta, Eris, Sedna, Haumea,
Makemake, Ixion, Orcus, Quaoar

## Lunar Nodes
| Point                    | Description |
|--------------------------|-------------|
| Mean_North_Lunar_Node    | Mean North Node (Rahu) |
| True_North_Lunar_Node    | True/Osculating North Node |
| Mean_South_Lunar_Node    | Mean South Node (Ketu) |
| True_South_Lunar_Node    | True/Osculating South Node |

## Lilith & Priapus Variants
| Point                | Description |
|----------------------|-------------|
| Mean_Lilith          | Mean Black Moon Lilith (default "Lilith") |
| True_Lilith          | Osculating apogee |
| Interpolated_Lilith  | Interpolated lunar apogee |
| Mean_Priapus         | Mean lunar perigee |
| True_Priapus         | Osculating perigee |
| Interpolated_Perigee | Interpolated perigee |

## Other Points
White_Moon (Selena), Earth, Vertex, Anti_Vertex

## Arabic Parts
| Point          | Aliases                     | Formula |
|----------------|-----------------------------|---------|
| Pars_Fortunae  | Part_of_Fortune, Lot_of_Fortune | ASC + Moon - Sun |
| Pars_Spiritus  | Part_of_Spirit, Lot_of_Spirit   | ASC + Sun - Moon |
| Pars_Amoris    | --                          | Part of Love |
| Pars_Fidei     | --                          | Part of Faith |

## Uranian / Hamburg School (v6)
Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon

## Fixed Stars
The full catalog (libephemeris, 1447 named stars) is exposed via
`GET /api/v6/fixed-stars/catalog`. There are no automatic defaults:
callers opt into specific stars per subject via `active_fixed_stars`
(at most 60 per request). All computed stars come back in
`subject.fixed_stars` as `KerykeionPointModel` entries.

## Axes (Angular Points)
Ascendant (ASC), Medium_Coeli (MC), Descendant (DESC), Imum_Coeli (IC)

Use `axis_orb_limit` to set a separate maximum orb for aspects involving
these angular points.

## Common Aliases
| Alias           | Canonical Name            |
|-----------------|---------------------------|
| mean_node       | Mean_North_Lunar_Node     |
| true_node       | True_North_Lunar_Node     |
| north_node      | Mean_North_Lunar_Node     |
| south_node      | Mean_South_Lunar_Node     |
| asc             | Ascendant                 |
| mc              | Medium_Coeli              |
| desc            | Descendant                |
| ic              | Imum_Coeli                |
| lilith          | Mean_Lilith               |
| part_of_fortune | Pars_Fortunae             |
| lot_of_fortune  | Pars_Fortunae             |
| part_of_spirit  | Pars_Spiritus             |
| lot_of_spirit   | Pars_Spiritus             |

Point names are case-insensitive and alias-aware in all API requests.
"""

    # ------------------------------------------------------------------
    # 6. Birth Chart Analysis Prompt
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://prompts/birth-chart-analysis")
    def birth_chart_analysis_prompt() -> str:
        return """\
# Birth Chart Analysis Template

Use this template when interpreting a natal birth chart from the Astrologer API.

## Step 1: Chart Overview
- Identify the Sun sign, Moon sign, and Ascendant (Rising sign).
- Note the element and modality balance from the distribution data.
- Identify the chart shape/pattern (bundle, bowl, bucket, splash, etc.).

## Step 2: Planetary Placements
- Analyze each planet by sign and house.
- Pay special attention to the chart ruler (ruler of the Ascendant sign).
- Note any planets in domicile or exaltation (strong) vs detriment or fall (challenged).
- Identify stelliums (3+ planets in one sign or house).

## Step 3: Aspects
- Start with tight aspects (small orbs) as they are the most influential.
- Focus on aspects involving personal planets (Sun, Moon, Mercury, Venus, Mars).
- Note major aspect patterns: Grand Trine, T-Square, Grand Cross, Yod, etc.

## Step 4: Essential Dignities (if calculate_dignities was enabled)
- Analyze essential dignity scores for each planet.
- Identify the most dignified and most debilitated planets.
- Consider Chaldean decan and Egyptian term rulers.

## Step 5: Vedic Lunar Mansions (if calculate_nakshatra was enabled)
- Note each planet's Nakshatra placement and pada.
- Identify the Vimsottari Dasha lord for timing context.
- Relate Nakshatra symbolism to the planet's expression.

## Step 6: Gauquelin Sectors (if calculate_gauquelin was enabled)
- Note planets in Gauquelin plus zones (near angles).
- Planets in sectors 1 (rising) or 10 (culminating) are statistically prominent.

## Step 7: Synthesis
- Weave the above into a coherent narrative.
- Identify core themes, strengths, and growth areas.
- Keep the tone constructive and empowering.
"""

    # ------------------------------------------------------------------
    # 7. Synastry Analysis Prompt
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://prompts/synastry-analysis")
    def synastry_analysis_prompt() -> str:
        return """\
# Synastry Analysis Template

Use this template when interpreting synastry (relationship comparison) data.

## Step 1: Cross-Aspects
- Identify the tightest inter-chart aspects first (smallest orbs).
- Focus on aspects between personal planets (Sun, Moon, Mercury, Venus, Mars).
- Note any planet-to-angle contacts (one person's planet on the other's ASC or MC).

## Step 2: House Overlays
- Check where Person A's planets fall in Person B's houses and vice versa.
- The house overlay shows which life area is activated by the other person.

## Step 3: Element & Modality Comparison
- Compare the element distributions of both charts.
- Shared element emphasis = natural compatibility; missing elements = growth edges.

## Step 4: Key Relationship Aspects
- Venus-Mars: physical and romantic attraction.
- Moon-Moon / Moon-Venus: emotional compatibility.
- Sun-Moon: identity-emotion harmony.
- Saturn contacts: commitment, longevity, and potential friction.
- Pluto contacts: intensity, transformation, power dynamics.

## Step 5: Composite Chart
Use the **Midpoint** composite for the relationship's emergent identity, or the
**Davison** composite for a time-anchored view of the relationship as an entity.
The Davison chart can be progressed and has a real date/location, making it
useful for timing relationship events.

## Step 6: Synthesis
- Balance strengths (harmonious aspects) with challenges (squares, oppositions).
- Identify the relationship's central themes and purpose.
- Offer practical insights for navigating differences.
"""

    # ------------------------------------------------------------------
    # 8. Transit Analysis Prompt
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://prompts/transit-analysis")
    def transit_analysis_prompt() -> str:
        return """\
# Transit Analysis Template

Use this template when interpreting transits to a natal chart.

## Step 1: Identify Active Transits
- List transiting planets and the natal points they aspect.
- Note the aspect type (conjunction, opposition, trine, square, sextile, etc.).
- Prioritize outer-planet transits (Pluto, Neptune, Uranus, Saturn) as they are
  slower and more transformative.

## Step 2: Transit Context
- Check the transiting planet's current sign and house position in the natal chart.
- Consider whether the transit is applying (approaching exact) or separating.

## Step 3: Time-Range Analysis
For deeper insight, use the specialized transit tools:
- **get_transit_events**: analyzes a date range and returns grouped events with
  applying start, exact moment, and separating end. Supports iterative
  refinement of the exact timing, down to sub-second at the maximum
  `refinement_iterations` (30).
- **get_transit_moments**: returns day-by-day snapshots of all active aspects
  between transiting and natal planets within a date range.

These tools are far more efficient than making repeated single-date calls.

## Step 4: Outer Planet Transits
- **Pluto**: deep transformation, power, rebirth (2-3 year transit to a point).
- **Neptune**: dissolution, spirituality, confusion (1-2 years).
- **Uranus**: sudden change, liberation, innovation (about 1 year).
- **Saturn**: structure, responsibility, maturation (several months).
- **Jupiter**: expansion, opportunity, growth (a few weeks to months).

## Step 5: Eclipses & Lunations
- Check if any recent or upcoming eclipses activate natal points.
- New/Full Moons near natal planets mark monthly activation points.

## Step 6: Synthesis
- Combine multiple active transits into an overall narrative.
- Note if several transits converge on the same natal point or house.
- Identify the central theme of the current period.
"""

    # ------------------------------------------------------------------
    # 9. Advanced Features Reference (NEW)
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/reference/advanced-features")
    def advanced_features_reference() -> str:
        return """\
# Advanced Features Reference

Advanced calculations use the domain-specific `/api/v6/*` endpoints.

## Eclipse Search
**Endpoint:** `POST /api/v6/events/eclipses`
Search for upcoming solar and lunar eclipses, globally or for a specific location.
- Parameters: `latitude`, `longitude` (optional, omit for global), `start_year`, `count`
- Returns: lists of solar and lunar eclipse events with dates, types, and magnitudes.

## Planetary Phenomena
**Endpoint:** `POST /api/v6/events/planetary-phenomena`
Compute observational data for planets at a given moment.
- Parameters: `subject`, `planets` (optional filter), `solar_phase_thresholds`
  (optional half-width overrides for the morning/evening-star classification;
  the applied values are echoed back)
- Returns: phase angle, elongation, magnitude, morning/evening star status.

## Planetary Nodes
**Endpoint:** `POST /api/v6/analysis/planetary-nodes`
Compute orbital node positions and apsides for planets.
- Parameters: `subject`, `method` ("mean" or "osculating"), `planets` (optional)
- Returns: ascending/descending node longitudes, perihelion/aphelion positions.

## Heliacal Events
**Endpoint:** `POST /api/v6/events/heliacal-events`
Find heliacal rising/setting events (first/last visibility near the Sun).
- Parameters: `subject` (location + start time), `count`, `planets` (optional),
  `event_types` (optional filter on rising/setting event kinds)
- Returns: list of heliacal events with dates and event types.

## Occultations
**Endpoint:** `POST /api/v6/events/occultations`
**Endpoint:** `POST /api/v6/events/occultations/global`
Search for occultations of a planet by the Moon.
- Parameters: `subject`, `planet` (the occulted body, default "Venus"), `count`
- Returns: list of occultation events. The local endpoint uses the subject's coordinates.

## Relocated Chart
**Endpoint:** `POST /api/v6/locational/relocated-chart`
Relocate a natal chart to a new geographic location. Planetary positions stay the
same; houses and angles are recalculated for the new location.
- Parameters: `subject`, `new_latitude`, `new_longitude`, `new_city`, `new_nation`, `new_timezone`, `active_points` (optional)
- Returns: relocated astrological subject data.

## Fixed Star Discovery
**Endpoint:** `POST /api/v6/fixed-stars/discovery`
Discover prominent fixed stars in conjunction with chart points.
- Parameters: `subject`, `orb` (default 1.0 degrees)
- Returns: list of stars with name, magnitude, constellation, conjuncting planet, and orb.

## Primary Directions
**Endpoint:** `POST /api/v6/predictive/primary-directions/analysis`
Compute primary directions using the Placidus semi-arc method.
- Parameters: `subject`, `max_years` (default 100), `rate_key` ("ptolemy" or "naibod"), `aspects`
- Returns: list of directed aspects with arc and date, plus speculum table.

## Astro-Cartography
**Endpoint:** `POST /api/v6/locational/astro-cartography`
Compute ACG planetary lines showing where planets are angular on the Earth.
- Parameters: `subject`, `step` (longitude resolution), `tolerance`, `lat_range_min/max`, `planets`
- Returns: list of ACG lines with planet, line type (ASC/DSC/MC/IC), and coordinate points.

## Declination Aspects
**Endpoint:** `POST /api/v6/analysis/declination-aspects`
**Endpoint:** `POST /api/v6/analysis/declination-aspects/dual`
Compute parallel and contra-parallel aspects based on declination.
- Parameters: `subject` (single) or `first_subject`/`second_subject` (dual), `active_points`, `orb`
- Returns: list of declination aspects.

## Transit Events
**Endpoint:** `POST /api/v6/transits/aspect-timeline`
Compute transit events over a date range with optional exact-moment refinement.
- Parameters: `subject`, `start_date`, `end_date`, `step_days`, `refine_exact_moments`,
  `refinement_iterations`, `active_points`, `active_aspects`
- Returns: grouped events with applying start, exact moment, and separating end.

## Transit Moments
**Endpoint:** `POST /api/v6/transits/daily-aspects`
Day-by-day snapshots of all active transit aspects within a date range.
- Parameters: same as transit_events.
- Returns: per-date list of active transiting aspects.

## Ephemeris
**Endpoint:** `POST /api/v6/ephemeris`
Generate an ephemeris table over a date range at configurable intervals.
- Parameters: `start_date`, `end_date`, `step_type` ("days"/"hours"/"minutes"),
  `step`, `latitude`, `longitude`, `timezone`, `is_dst`, zodiac/sidereal/house config,
  `active_points`, `active_fixed_stars`, `include_houses`, `omit_nulls`.
- Returns: list of ephemeris data points with planetary positions and house cusps.

## Report Generation
**Endpoint:** `POST /api/v6/reports`
Generate a human-readable text report for an astrological subject.
- Parameters: `subject`, `include_aspects` (optional), `max_aspects` (optional),
  `chart_type` (optional), `second_subject` (optional, for dual-chart reports)
- Returns: formatted text report string.

## Heliocentric Return
**Endpoint:** `POST /api/v6/returns/heliocentric/chart`
**Endpoint:** `POST /api/v6/returns/heliocentric/data`
Compute a heliocentric return chart (planet returns to natal heliocentric longitude).
- Parameters: `subject`, `planet`, `wheel_type` ("single" or "dual"),
  `year` or `iso_datetime` (anchor for the search), `direction` ("next" or
  "previous"), `return_location` (optional relocation of the return),
  rendering config
- Returns: return chart data (and SVG for the chart endpoint).

## Lunar Node Crossing
**Endpoint:** `POST /api/v6/returns/lunar-node-crossing/chart`
**Endpoint:** `POST /api/v6/returns/lunar-node-crossing/data`
Compute a lunar node crossing chart (the Moon crossing its own node,
ecliptic latitude zero) -- the next or the previous one depending on
`direction`.
- Parameters: `subject`, `wheel_type`, `year` or `iso_datetime` (anchor for
  the search), `direction` ("next" or "previous"), `return_location`
  (optional relocation), rendering config
- Returns: node crossing chart data (and SVG for the chart endpoint).

## More Tools (compact reference)

| Tool -- REST endpoint | What it computes |
|-----------------------|------------------|
| `get_lunations` -- `POST /api/v6/events/lunations` | New / First Quarter / Full / Last Quarter moments in a date range |
| `get_retrograde_stations` -- `POST /api/v6/events/retrograde-stations` | Retrograde/direct stations (motion reversals) in a date range |
| `get_sign_ingresses` -- `POST /api/v6/events/sign-ingresses` | Zodiac sign ingresses (30-degree boundary crossings) in a date range |
| `get_midpoints` -- `POST /api/v6/analysis/midpoints` | Full midpoint table for a chart |
| `get_zodiacal_releasing` -- `POST /api/v6/traditional/zodiacal-releasing` | Zodiacal releasing (aphesis) periods from Fortune or Spirit |
| `get_profections` -- `POST /api/v6/traditional/profections` | Annual profections (Hellenistic year-lord technique) |
| `get_firdaria` -- `POST /api/v6/traditional/firdaria` | Firdaria (Persian time-lord) periods |
| `get_horary_indicators` -- `POST /api/v6/traditional/horary-indicators` | Horary significators and considerations before judgment |
| `get_secondary_progressions` -- `POST /api/v6/predictive/secondary-progressions/analysis` | Day-for-a-year progressed chart for a target moment (data) |
| `get_solar_arc_directions` -- `POST /api/v6/predictive/solar-arc-directions/analysis` | Solar arc directed chart for a target moment (data) |
| `get_transit_batch` -- `POST /api/v6/transits/batch` | Batch transit snapshots over a date range |
| `get_dominants` -- `POST /api/v6/analysis/dominants` | Dominant planet, sign, element, modality, house |
| `get_void_of_course_moon` -- `POST /api/v6/moon/void-of-course` | Void-of-course Moon for a single moment |
| `get_sun_times` -- `POST /api/v6/sun/times` | Sunrise, sunset, solar noon, day length |
| `get_planetary_hours` -- `POST /api/v6/sun/planetary-hours` | The 24 Chaldean planetary hours for a planetary day |

## Not Exposed via MCP (REST only)

- `POST /api/v6/calendar` -- daily astro calendar (lunations, ingresses, VoC, sign/retrograde periods)
- `POST /api/v6/events/mundane-aspects` -- sky-to-sky aspects for a moment
- `POST /api/v6/moon/void-of-course/windows` -- void-of-course windows over a date range
- `GET /api/v6/fixed-stars/catalog` -- the full fixed-star catalog (1447 names)
- the `/context/*` variants of secondary-progressions, solar-arc-directions, midpoints and primary-directions (the MCP twins return data without `include_ai_context`)
- the SVG renderings of `/chart/secondary-progressions` and `/chart/solar-arc-directions` (the MCP tools return data only)
"""

    # ------------------------------------------------------------------
    # 10. Moon Phase Reference (NEW)
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/reference/moon-phases")
    def moon_phase_reference() -> str:
        return """\
# Moon Phase Reference

## Endpoints
- `POST /api/v6/moon-phase` -- Moon phase for a specific date/time and location
- `POST /api/v6/moon-phase/context` -- Same data with AI-optimized XML context
- `POST /api/v6/moon-phase/now-utc` -- Current moon phase at Greenwich (UTC)
- `POST /api/v6/moon-phase/now-utc/context` -- Current phase with AI context

## Parameters
| Field          | Type  | Required | Description |
|----------------|-------|----------|-------------|
| year           | int   | yes      | Year |
| month          | int   | yes      | Month |
| day            | int   | yes      | Day |
| hour           | int   | yes      | Hour (0-23) |
| minute         | int   | yes      | Minute (0-59) |
| second         | int   | no       | Second (default 0) |
| latitude       | float | yes      | Observer latitude |
| longitude      | float | yes      | Observer longitude |
| timezone       | str   | yes      | IANA timezone |
| location_precision | int | no    | Decimal precision for coordinates in response (default 0) |

The `/now-utc` endpoints require no date/location parameters.

## What the Moon Phase Tool Returns
- **Phase name**: New Moon, Waxing Crescent, First Quarter, Waxing Gibbous,
  Full Moon, Waning Gibbous, Last Quarter, Waning Crescent.
- **Illumination**: percentage of the Moon's visible surface illuminated (0-100%).
- **Moon age**: days since the last New Moon.
- **Stage**: "Waxing" or "Waning".
- **Moon sign**: zodiac sign and degree of the Moon.
- **Sun sign**: zodiac sign and degree of the Sun.
- **Upcoming major phases**: dates of the next New Moon, First Quarter,
  Full Moon, and Last Quarter.
- **Next eclipses**: date and type of the next solar and lunar eclipse.
- **Sunrise / Sunset**: times for the observer's location.

## Phase Meanings
| Phase             | Keywords |
|-------------------|----------|
| New Moon          | Beginnings, intention setting, planting seeds |
| Waxing Crescent   | Emergence, momentum, building |
| First Quarter     | Action, challenge, decision point |
| Waxing Gibbous    | Refinement, adjustment, anticipation |
| Full Moon         | Culmination, illumination, harvest |
| Waning Gibbous    | Gratitude, sharing, dissemination |
| Last Quarter      | Release, re-evaluation, letting go |
| Waning Crescent   | Rest, surrender, reflection, composting |

## Use Cases
- Daily lunar awareness for planning and intention-setting.
- Gardening and agricultural timing.
- Emotional and energetic cycle tracking.
- Ritual and spiritual practice timing.
- Eclipse awareness and preparation.
"""

    # ------------------------------------------------------------------
    # 11. Moon Phase Analysis Prompt (NEW)
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://prompts/moon-phase-analysis")
    def moon_phase_analysis_prompt() -> str:
        return """\
# Moon Phase Analysis Template

Use this template when interpreting moon phase data from the Astrologer API.

## Step 1: Current Phase
- State the current lunar phase name and illumination percentage.
- Describe the phase's general significance (see phase meanings in the
  moon-phases reference resource).
- Note whether the Moon is waxing (growing toward Full) or waning (receding
  toward New).

## Step 2: Moon's Zodiac Sign
- Identify the Moon's current zodiac sign and degree.
- Describe the emotional and energetic qualities of the Moon in this sign.
- If the Moon is near the boundary of a sign, mention the upcoming sign change.

## Step 3: Sun-Moon Relationship
- Note the angular distance between Sun and Moon (this determines the phase).
- Consider the element and modality relationship between the Sun and Moon signs.
- A harmonious element pairing (e.g. Fire-Air, Earth-Water) suggests flow;
  a challenging one suggests creative tension.

## Step 4: Upcoming Phases
- Mention the dates of the next major phases (New Moon, First Quarter,
  Full Moon, Last Quarter).
- Highlight which zodiac signs these upcoming phases fall in.
- Suggest what themes each upcoming phase may activate.

## Step 5: Eclipse Awareness
- If an eclipse is approaching (within the next 30 days), flag it prominently.
- Solar eclipses (at New Moon) intensify new beginnings and can bring
  unexpected changes.
- Lunar eclipses (at Full Moon) intensify release and revelation themes.
- Eclipses near natal points are especially significant.

## Step 6: Practical Guidance
- Offer concrete suggestions aligned with the current phase:
  - New Moon: set intentions, start projects.
  - Waxing phases: take action, build momentum.
  - Full Moon: celebrate, harvest, bring things to completion.
  - Waning phases: review, release, rest.
"""

    # ------------------------------------------------------------------
    # 12. Solar Return Analysis Prompt (NEW)
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://prompts/solar-return-analysis")
    def solar_return_analysis_prompt() -> str:
        return """\
# Solar Return Analysis Template

Use this template when interpreting a solar return chart. The solar return is
cast for the exact moment the transiting Sun returns to its natal degree each
year, and it describes the themes and energies of the coming year.

## Step 1: Sun House Placement
- The house the Sun occupies in the solar return chart is the primary focus
  area for the year.
- This is the single most important factor in the solar return.
- Examples: Sun in the 10th = career-focused year; Sun in the 7th = relationships;
  Sun in the 4th = home, family, inner foundations.

## Step 2: Ascendant & Chart Ruler
- The solar return Ascendant sets the tone for how the year unfolds.
- Identify the ruler of the solar return Ascendant and note its house and sign.
- This planet acts as the "guide" for the year's energy.

## Step 3: Moon Placement
- The Moon's sign and house show the emotional tone and where feelings are directed.
- Moon phase in the solar return: New Moon years = fresh starts; Full Moon years
  = culmination and visibility.

## Step 4: Planetary Positions
- Analyze key planets by house (and sign if notably different from natal).
- Pay attention to planets near angles (ASC, MC, DSC, IC) as they are
  especially prominent.
- Note any planets that have changed houses compared to the natal chart.

## Step 5: Aspects in the Solar Return
- Focus on tight aspects involving the Sun, Moon, and Ascendant ruler.
- Challenging aspects (squares, oppositions) show areas of growth and tension.
- Harmonious aspects (trines, sextiles) show areas of ease and support.

## Step 6: Comparison with Natal Chart
- Compare solar return planetary positions to natal positions.
- Note if any solar return planets conjunct natal angles or key natal planets.
- Identify which natal houses are activated by the solar return planets.

## Step 7: Year Themes
- Synthesize the above into 2-3 core themes for the year.
- Be specific: rather than "a good year," identify what area of life is
  highlighted and what kind of growth or change is indicated.
- Note the approximate timing: planets near the MC may peak mid-year;
  planets near the IC may be more prominent at the start/end of the solar year.
"""

    # ------------------------------------------------------------------
    # 13. MCP Quick Start
    # ------------------------------------------------------------------
    @mcp.resource("astrologer://docs/mcp-quick-start")
    def mcp_quick_start() -> str:
        return """\
# Astrologer MCP Quick Start

Minimal working examples for the most common tools.
All examples use **offline mode** (latitude + longitude + timezone).

## Birth Chart (flat parameters)
```json
{
  "name": "get_birth_chart",
  "arguments": {
    "name": "John",
    "year": 1990, "month": 6, "day": 15,
    "hour": 14, "minute": 30,
    "city": "Rome", "nation": "IT",
    "timezone": "Europe/Rome",
    "latitude": 41.9028, "longitude": 12.4964
  }
}
```

## Subject (flat parameters)
```json
{
  "name": "get_subject",
  "arguments": {
    "name": "Jane",
    "year": 1985, "month": 12, "day": 1,
    "hour": 8, "minute": 0,
    "city": "London", "nation": "GB",
    "timezone": "Europe/London",
    "latitude": 51.5074, "longitude": -0.1278
  }
}
```

## Synastry (two subject objects)
```json
{
  "name": "get_synastry",
  "arguments": {
    "first_subject": {
      "name": "Person A",
      "year": 1990, "month": 6, "day": 15,
      "hour": 14, "minute": 30,
      "city": "Rome", "nation": "IT",
      "timezone": "Europe/Rome",
      "latitude": 41.9028, "longitude": 12.4964
    },
    "second_subject": {
      "name": "Person B",
      "year": 1992, "month": 3, "day": 10,
      "hour": 8, "minute": 0,
      "city": "Milan", "nation": "IT",
      "timezone": "Europe/Rome",
      "latitude": 45.4642, "longitude": 9.19
    }
  }
}
```

## Solar Return (subject object + year)
```json
{
  "name": "get_solar_return",
  "arguments": {
    "subject": {
      "name": "John",
      "year": 1990, "month": 6, "day": 15,
      "hour": 14, "minute": 30,
      "city": "Rome", "nation": "IT",
      "timezone": "Europe/Rome",
      "latitude": 41.9028, "longitude": 12.4964
    },
    "year": 2026
  }
}
```

## Planetary Phenomena (subject object)
```json
{
  "name": "get_planetary_phenomena",
  "arguments": {
    "subject": {
      "name": "Test",
      "year": 2025, "month": 1, "day": 1,
      "hour": 12, "minute": 0,
      "city": "London", "nation": "GB",
      "timezone": "Etc/UTC",
      "latitude": 51.4769, "longitude": 0.0005
    }
  }
}
```

## Transit Events (subject + date range)
```json
{
  "name": "get_transit_events",
  "arguments": {
    "subject": {
      "name": "John",
      "year": 1990, "month": 6, "day": 15,
      "hour": 14, "minute": 30,
      "city": "Rome", "nation": "IT",
      "timezone": "Europe/Rome",
      "latitude": 41.9028, "longitude": 12.4964
    },
    "start_date": "2026-01-01",
    "end_date": "2026-03-01"
  }
}
```

## Eclipses (no subject needed)
```json
{
  "name": "get_eclipses",
  "arguments": {
    "start_year": 2025,
    "count": 5
  }
}
```

## Current Moment (no arguments needed)
```json
{
  "name": "get_current_moment",
  "arguments": {}
}
```

## Key Notes
- **Subject fields**: `name`, `year`, `month`, `day`, `hour`, `minute`, `city` are required.
- **Location**: Provide `latitude` + `longitude` + `timezone` (offline) OR `geonames_username` (online).
- **omit_nulls**: Defaults to `true` for compact responses. Set `false` for full payloads.
- **include_ai_context**: Defaults to `true`. Includes LLM-optimized text summary.
"""
