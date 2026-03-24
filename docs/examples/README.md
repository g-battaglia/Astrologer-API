---
title: 'API Examples'
description: 'Complete request and response examples for every Astrologer API v5 endpoint. Organized by category with chart previews.'
order: 0
---

# API Examples

Complete request/response examples for every Astrologer API v5 endpoint. Each example includes a full JSON request body and the corresponding response payload.

> **Note:** Chart SVG examples include a visual preview rendered from the [test baselines](https://github.com/g-battaglia/Astrologer-API/tree/v5/tests/baselines).

---

## Chart Endpoints (SVG)

Endpoints that return rendered SVG chart images along with calculated data.

| Chart Type | Example | Preview |
|------------|---------|---------|
| **Natal Chart** | [View Example](natal_chart_svg) | ![Natal](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_natal.svg) |
| **Now Chart** | [View Example](now_chart_svg) | ![Now](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/now_chart.svg) |
| **Synastry Chart** | [View Example](synastry_chart_svg) | ![Synastry](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_synastry.svg) |
| **Composite Chart** | [View Example](composite_chart_svg) | ![Composite](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_composite.svg) |
| **Transit Chart** | [View Example](transit_chart_svg) | ![Transit](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_transit.svg) |
| **Solar Return Chart** | [View Example](solar_return_chart_svg) | ![Solar Return](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_solar_return.svg) |
| **Lunar Return Chart** | [View Example](lunar_return_chart_svg) | ![Lunar Return](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/v5/tests/baselines/chart_lunar_return.svg) |

---

## Data Endpoints (JSON)

Endpoints that return raw calculated data without visual charts. Ideal for custom rendering or analysis.

### Subject Data

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/subject` | [View Example](subject) | Calculate a subject's astrological data from birth info. |
| `POST /api/v5/now/subject` | [View Example](now_subject) | Get the current moment's astrological data (UTC/Greenwich). |

### Chart Data

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/chart-data/birth-chart` | [View Example](natal_chart_data) | Full natal chart calculations (planets, houses, aspects, distributions). |
| `POST /api/v5/chart-data/synastry` | [View Example](synastry_chart_data) | Synastry data comparing two subjects. |
| `POST /api/v5/chart-data/composite` | [View Example](composite_chart_data) | Composite midpoint chart data for two subjects. |
| `POST /api/v5/chart-data/transit` | [View Example](transit_chart_data) | Transit data comparing natal vs. transit moment. |
| `POST /api/v5/chart-data/solar-return` | [View Example](solar_return_chart_data) | Solar return chart data for a given year. |
| `POST /api/v5/chart-data/lunar-return` | [View Example](lunar_return_chart_data) | Lunar return chart data for a given period. |

### Compatibility

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/compatibility-score` | [View Example](compatibility_score) | Ciro Discepolo compatibility score between two subjects. |

---

## Moon Phase Endpoints

Dedicated endpoints for detailed lunar phase analysis, using a simplified request model (no `subject` wrapper).

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/moon-phase` | [View Example](moon_phase) | Detailed moon phase for a specific date/time and location. |
| `POST /api/v5/moon-phase/now-utc` | [View Example](moon_phase_now_utc) | Current moon phase at Greenwich (no request body needed). |
| `POST /api/v5/moon-phase/context` | [View Example](moon_phase_context) | Moon phase with AI-optimized XML context. |
| `POST /api/v5/moon-phase/now-utc/context` | [View Example](moon_phase_now_utc_context) | Current moon phase with AI-optimized XML context. |

---

## Context Endpoints (AI)

Endpoints that return AI-optimized XML interpretations along with the calculated data. Designed for injection into LLM prompts.

### Subject Context

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/context/subject` | [View Example](subject_context) | Subject planetary positions with AI-structured XML context. |
| `POST /api/v5/now/context` | [View Example](now_context) | Current moment with AI-structured XML context. |

### Chart Context

| Endpoint | Example | Description |
|----------|---------|-------------|
| `POST /api/v5/context/birth-chart` | [View Example](natal_context) | Natal chart with full AI interpretation (aspects, distributions, houses). |
| `POST /api/v5/context/synastry` | [View Example](synastry_context) | Synastry comparison with AI relationship analysis. |
| `POST /api/v5/context/composite` | [View Example](composite_context) | Composite chart with AI relationship-entity analysis. |
| `POST /api/v5/context/transit` | [View Example](transit_context) | Transit chart with AI predictive analysis. |
| `POST /api/v5/context/solar-return` | [View Example](solar_return_context) | Solar return with AI yearly forecast context. |
| `POST /api/v5/context/lunar-return` | [View Example](lunar_return_context) | Lunar return with AI monthly forecast context. |
