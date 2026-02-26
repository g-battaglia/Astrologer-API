---
title: 'Astrologer API Documentation'
description: 'Explore the Astrologer API v5 documentation. A comprehensive engine for high-precision astrological calculations, SVG chart rendering, and AI-driven interpretations.'
---

# Astrologer API v5 Documentation

## Overview

The **Astrologer API v5** is a comprehensive engine designed for high-precision astrological calculations, professional-grade chart rendering, and AI-driven interpretations. It serves as a robust backend for astrology applications, enabling developers to integrate complex astrological features without needing deep domain expertise.

The API provides three main capabilities:

1.  **Ephemeris Calculations**: Computes accurate positions of planets, house cusps, and other celestial points using the Swiss Ephemeris (via the Kerykeion library).
2.  **SVG Chart Generation**: Generates high-quality, ready-to-display SVG charts for various astrological techniques (Natal, Synastry, Composite, Transits).
3.  **AI Context**: Leverages Generative AI to provide XML-structured explanations, syntheses, and personalized interpretations based on the calculated astrological data.

## Core Concepts

### The "Subject"

The fundamental unit of the API is the **Subject**. A Subject represents a specific entity (person, event, or moment) defined by a time and a location on Earth. Almost every endpoint requires one or more `subject` objects to perform calculations.

A typical `subject` object includes:

-   **Date & Time**: Year, month, day, hour, minute.
-   **Location**: City, nation, latitude, longitude.
-   **Timezone**: IANA timezone string (e.g., "Europe/London").
-   **Settings**: Zodiac type (Tropical/Sidereal), house system, etc.

### Chart Types

The API supports several standard astrological chart types:

-   **Natal Chart**: A map of the sky at a single moment (e.g., a birth).
-   **Synastry Chart**: A bi-wheel chart comparing two subjects to analyze their relationship dynamics.
-   **Composite Chart**: A single-wheel chart derived from the midpoints of two subjects, representing the relationship as a third entity.
-   **Transit Chart**: A bi-wheel chart comparing a natal subject with the current (or future) sky to forecast trends.
-   **Solar/Lunar Returns**: Charts calculated for the moment the Sun or Moon returns to its exact natal position.

## Base URL

All endpoints are prefixed with `/api/v5`.

## Authentication

Currently, the API is open for internal use. Future versions may require API keys or OAuth tokens.

## Error Handling

The API uses standard HTTP status codes:

-   **200 OK**: Success.
-   **400 Bad Request**: Invalid request parameters.
-   **422 Unprocessable Entity**: Validation error (e.g., invalid date or missing field).
-   **500 Internal Server Error**: Unexpected server error.

## Documentation Index

### 📊 Data Endpoints (JSON)

Endpoints that return raw calculated data (JSON) without visual charts. Ideal for custom frontend rendering or data analysis.

-   [**Subject**](data/subject.md) ([Example](examples/subject.md)): Calculate a subject's astrological data.
-   [**Now Subject**](data/now_subject.md) ([Example](examples/now_subject.md)): Get the astrological data for the current moment.
-   [**Compatibility Score**](data/compatibility_score.md) ([Example](examples/compatibility_score.md)): Calculate a numerical compatibility score between two people.
-   **Chart Data**:
    -   [Natal Chart Data](data/chart_data_natal.md) ([Example](examples/natal_chart_data.md))
    -   [Synastry Chart Data](data/chart_data_synastry.md) ([Example](examples/synastry_chart_data.md))
    -   [Composite Chart Data](data/chart_data_composite.md) ([Example](examples/composite_chart_data.md))
    -   [Transit Chart Data](data/chart_data_transit.md) ([Example](examples/transit_chart_data.md))
    -   [Solar Return Data](data/chart_data_solar_return.md) ([Example](examples/solar_return_chart_data.md))
    -   [Lunar Return Data](data/chart_data_lunar_return.md) ([Example](examples/lunar_return_chart_data.md))

### 🌙 Moon Phase Endpoints

Dedicated endpoints for detailed lunar phase analysis, using a simplified request model (no `subject` wrapper).

-   [**Moon Phase**](data/moon_phase.md) ([Example](examples/moon_phase.md)): Detailed moon phase for a specific date/time and location.
-   [**Moon Phase Now (UTC)**](data/moon_phase_now_utc.md) ([Example](examples/moon_phase_now_utc.md)): Current moon phase at Greenwich.
-   [**Moon Phase Context**](context/moon_phase_context.md) ([Example](examples/moon_phase_context.md)): Moon phase with AI-optimized XML context.
-   [**Moon Phase Now Context (UTC)**](context/moon_phase_now_utc_context.md) ([Example](examples/moon_phase_now_utc_context.md)): Current moon phase with AI-optimized XML context.

### 🎨 Chart Endpoints (SVG)

Endpoints that return rendered SVG charts along with the calculation data.

-   [**Natal Chart**](charts/natal_chart.md) ([Example](examples/natal_chart_svg.md))
-   [**Now Chart**](charts/now_chart.md) ([Example](examples/now_chart_svg.md))
-   [**Synastry Chart**](charts/synastry_chart.md) ([Example](examples/synastry_chart_svg.md))
-   [**Composite Chart**](charts/composite_chart.md) ([Example](examples/composite_chart_svg.md))
-   [**Transit Chart**](charts/transit_chart.md) ([Example](examples/transit_chart_svg.md))
-   [**Solar Return Chart**](charts/solar_return_chart.md) ([Example](examples/solar_return_chart_svg.md))
-   [**Lunar Return Chart**](charts/lunar_return_chart.md) ([Example](examples/lunar_return_chart_svg.md))

### 🧠 Context Endpoints (AI)

Endpoints that return AI-optimized XML interpretations and context.

-   [**Subject Context**](context/subject_context.md) ([Example](examples/subject_context.md))
-   [**Now Context**](context/now_context.md) ([Example](examples/now_context.md))
-   [**Natal Chart Context**](context/natal_context.md) ([Example](examples/natal_context.md))
-   [**Synastry Context**](context/synastry_context.md) ([Example](examples/synastry_context.md))
-   [**Composite Context**](context/composite_context.md) ([Example](examples/composite_context.md))
-   [**Transit Context**](context/transit_context.md) ([Example](examples/transit_context.md))
-   [**Solar Return Context**](context/solar_return_context.md) ([Example](examples/solar_return_context.md))
-   [**Lunar Return Context**](context/lunar_return_context.md) ([Example](examples/lunar_return_context.md))

---

_Note: Miscellaneous endpoints (health checks) are available but not documented here._
