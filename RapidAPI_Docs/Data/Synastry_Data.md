## Endpoint

/api/v5/chart-data/synastry

## Name

Synastry Data

## Description

Returns synastry comparison data between two subjects, including aspects between their planets, house overlays, and a relationship compatibility score. Does not include SVG rendering.

### Parameters

-   `first_subject` (JSON object, required): The first subject's birth data.
-   `second_subject` (JSON object, required): The second subject's birth data.
-   `include_house_comparison` (boolean, optional): Include house overlay data.
-   `include_relationship_score` (boolean, optional): Calculate and return the compatibility score.
-   `active_points` (array, optional): Points to include.
-   `active_aspects` (array, optional): Aspects to include.
-   `distribution_method` (string, optional): Distribution calculation method.

## Request Body Example

```json
{
    "first_subject": {
        "name": "Partner A",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "city": "New York",
        "nation": "US",
        "longitude": -74.006,
        "latitude": 40.7128,
        "timezone": "America/New_York"
    },
    "second_subject": {
        "name": "Partner B",
        "year": 1992,
        "month": 5,
        "day": 20,
        "hour": 18,
        "minute": 30,
        "city": "Los Angeles",
        "nation": "US",
        "longitude": -118.2437,
        "latitude": 34.0522,
        "timezone": "America/Los_Angeles"
    },
    "include_house_comparison": true,
    "include_relationship_score": true
}
```

## Response Body Example

```json
{
    "status": "OK",
    "chart_data": {
        "chart_type": "Synastry",
        "first_subject": { "name": "Partner A" },
        "second_subject": { "name": "Partner B" },
        "aspects": [
            {
                "p1_name": "Sun",
                "p2_name": "Moon",
                "aspect": "conjunction",
                "orb": 2.5
            }
        ],
        "house_comparison": {
            "first_points_in_second_houses": [],
            "second_points_in_first_houses": []
        },
        "relationship_score": {
            "score_value": 11,
            "score_description": "Very Important",
            "is_destiny_sign": false,
            "score_breakdown": [
                {
                    "rule": "sun_moon_conjunction",
                    "description": "Sun-Moon conjunction (high precision)",
                    "points": 11,
                    "details": "Sun-Moon conjunction (orbit: 1.34°)"
                }
            ]
        }
    }
}
```
