---
title: 'Synastry Chart'
description: 'Visualize relationship compatibility with dual-wheel synastry charts. High-quality SVG rendering with house overlays and inter-aspect analysis.'
order: 3
---

# Synastry Chart Endpoint

## `POST /api/v5/chart/synastry`

> **📘 [View Complete Example](../examples/synastry_chart_svg.md)**

This endpoint generates a **synastry chart** (relationship compatibility chart) as a dual-wheel SVG visualization. Synastry is the astrological technique of comparing two birth charts to analyze relationship dynamics, compatibility, and potential challenges between two people.

The chart displays:

-   **Inner Wheel**: The first subject's natal chart
-   **Outer Wheel**: The second subject's natal chart
-   **Inter-Aspects**: The astrological aspects (connections) between the two charts
-   **Optional House Comparison Table**: Shows how each person's planets fall into the other's houses

**Use cases:**

-   **Romantic Compatibility Analysis**: Evaluate relationship potential between partners
-   **Business Partnerships**: Assess professional compatibility
-   **Family Dynamics**: Understand parent-child or sibling relationships
-   **Friendship Analysis**: Explore platonic connections
-   **Coaching & Counseling**: Provide visual aids for relationship therapy

The synastry chart reveals how two individuals interact on an energetic level, highlighting areas of harmony (trines, sextiles) and challenge (squares, oppositions). This is one of the most requested chart types in professional astrology practice.

### Request Body

-   **`first_subject`** (object, required): Inner wheel subject.
    ```json
    {
        "name": "Inner",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    }
    ```
-   **`second_subject`** (object, required): Outer wheel subject.
    ```json
    {
        "name": "Outer",
        "year": 1992,
        "month": 5,
        "day": 15,
        "hour": 18,
        "minute": 30,
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    }
    ```
-   **`theme`**, **`language`**, **`split_chart`** (rendering options).
-   **`style`** (string, optional): Chart wheel layout — "classic" (default) or "modern". Default: "classic".
-   **`show_zodiac_background_ring`** (bool, optional): Show colored zodiac wedges behind the wheel, modern style only. Default: true.
-   **`double_chart_aspect_grid_type`** (string, optional): Aspect display for dual charts — "list" (default) or "table". Default: "list".
-   **`show_house_position_comparison`** (bool, optional): Display house table (default: true).
-   **`show_cusp_position_comparison`** (bool, optional): Display cusp comparison grids for both subjects (default: true).
-   **`show_degree_indicators`** (bool, optional): Display radial lines and degree numbers for planet positions on the wheels (default: true).
-   **`show_aspect_icons`** (bool, optional): Display aspect icons on aspect lines (default: true).

#### Complete Request Example

```json
{
    "first_subject": {
        "name": "Inner",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "London",
        "nation": "GB",
        "longitude": -0.1278,
        "latitude": 51.5074,
        "timezone": "Europe/London"
    },
    "second_subject": {
        "name": "Outer",
        "year": 1992,
        "month": 5,
        "day": 15,
        "hour": 18,
        "minute": 30,
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    },
    "theme": "classic",
    "style": "modern",
    "show_zodiac_background_ring": true,
    "double_chart_aspect_grid_type": "list",
    "split_chart": true
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): Synastry data.
-   **`chart_wheel`** (string): SVG of the dual wheel.
-   **`chart_grid`** (string): SVG of the aspect grid.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart_wheel": "<svg ...> ... </svg>",
  "chart_grid": "<svg ...> ... </svg>"
}
```
