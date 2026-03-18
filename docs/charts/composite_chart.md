---
title: 'Composite Chart'
description: 'Visualize the unified essence of a partnership with SVG Composite charts. Midpoint-based single-wheel rendering for deep relationship analysis.'
order: 4
---

# Composite Chart Endpoint

## `POST /api/v5/chart/composite`

> **📘 [View Complete Example](../examples/composite_chart_svg.md)**

This endpoint generates a **composite chart** as a single-wheel SVG visualization. Unlike synastry (which compares two separate charts), a composite chart creates a completely new chart by calculating the mathematical midpoints between the two subjects' planetary positions. This resulting chart represents the relationship itself as a unique entity.

**Key Concept**:
The composite chart answers the question: "What is the nature of _this_ relationship?" rather than "How do these two people interact?" It symbolizes the relationship's purpose, destiny, and core characteristics.

**Calculation Method**:

-   Each planet's position is the midpoint between the two subjects' corresponding planets
-   House cusps are similarly calculated from midpoints
-   The result is a standalone chart representing the relationship's "soul"

**Use cases:**

-   **Relationship Purpose Analysis**: Understand the deeper meaning and mission of a partnership
-   **Couple's Counseling**: Explore the relationship's inherent strengths and challenges
-   **Business Ventures**: Analyze the potential and character of a partnership
-   **Long-term Forecasting**: See how the relationship evolves through transits to the composite chart

The composite chart is particularly valuable for committed relationships, as it provides insights that synastry alone cannot reveal. It's considered essential reading for couples seeking to understand their union's spiritual and practical dimensions.

### Request Body

-   **`first_subject`** (object, required): First partner.
    ```json
    {
        "name": "Partner A",
        "year": 1980,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "Rome",
        "nation": "IT",
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome"
    }
    ```
-   **`second_subject`** (object, required): Second partner.
    ```json
    {
        "name": "Partner B",
        "year": 1982,
        "month": 3,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Milan",
        "nation": "IT",
        "longitude": 9.19,
        "latitude": 45.4642,
        "timezone": "Europe/Rome"
    }
    ```
-   **`theme`**, **`language`**, **`split_chart`** (rendering options).
-   **`style`** (string, optional): Chart wheel layout — "classic" (default) or "modern". Default: "classic".
-   **`show_zodiac_background_ring`** (bool, optional): Show colored zodiac wedges behind the wheel, modern style only. Default: true.
-   **`double_chart_aspect_grid_type`** (string, optional): Aspect display layout — "list" (default) or "table". Default: "list".
-   **`show_house_position_comparison`** (bool, optional): Show or hide the house/points comparison table for the composite chart (default: true).
-   **`show_degree_indicators`** (bool, optional): Display radial lines and degree numbers for planet positions on the wheel (default: true).
-   **`show_aspect_icons`** (bool, optional): Display aspect icons on aspect lines (default: true).

#### Complete Request Example

```json
{
    "first_subject": {
        "name": "Partner A",
        "year": 1980,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "Rome",
        "nation": "IT",
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome"
    },
    "second_subject": {
        "name": "Partner B",
        "year": 1982,
        "month": 3,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Milan",
        "nation": "IT",
        "longitude": 9.19,
        "latitude": 45.4642,
        "timezone": "Europe/Rome"
    },
    "theme": "dark",
    "style": "modern",
    "show_zodiac_background_ring": true
}
```

### Response Body

-   **`status`** (string): "OK".
-   **`chart_data`** (object): Composite data.
-   **`chart`** (string): SVG string.

#### Complete Response Example

```json
{
  "status": "OK",
  "chart_data": { ... },
  "chart": "<svg ...> ... </svg>"
}
```
