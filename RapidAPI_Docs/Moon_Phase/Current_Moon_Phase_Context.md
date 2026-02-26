## Endpoint
/api/v5/moon-phase/now-utc/context

## Name

Current Moon Phase - AI Context

## Description

Returns detailed moon phase information for the current UTC moment at Greenwich Observatory (51.4779°N, 0.0015°W) with an AI-optimized XML context string. This is the context variant of `/api/v5/moon-phase/now-utc`.

All request fields are optional. An empty JSON body `{}` is valid. Only `using_default_location` and `location_precision` are accepted — any other field will be rejected with a 422 error.

All times in the response (sunrise, sunset, etc.) are in UTC.

### Parameters

-   `using_default_location` (boolean, optional): Metadata flag (default: true).
-   `location_precision` (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: 0). Display rounding only.

## Request Body Example

```json
{}
```

## Response Body Example

```json
{
    "status": "OK",
    "context": "<moon_phase_overview timestamp=\"...\" datestamp=\"...\">...</moon_phase_overview>",
    "moon_phase_overview": {
        "timestamp": 1717245000,
        "datestamp": "Sat, 01 Jun 2024 12:30:00 +0000",
        "sun": {
            "sunrise": 1717213706,
            "sunrise_timestamp": "03:48",
            "sunset": 1717272482,
            "sunset_timestamp": "20:08",
            "solar_noon": "11:58",
            "day_length": "16:20",
            "position": {
                "altitude": 60.03,
                "azimuth": 194.99,
                "distance": 151708222.77
            },
            "next_solar_eclipse": {
                "timestamp": 1727894704,
                "datestamp": "Wed, 02 Oct 2024 18:45:04 +0000",
                "type": "Annular Solar Eclipse",
                "visibility_regions": null
            }
        },
        "moon": {
            "phase": 0.816,
            "phase_name": "Waning Crescent",
            "major_phase": "Last Quarter",
            "stage": "waning",
            "illumination": "30%",
            "age_days": 9,
            "lunar_cycle": "81.627%",
            "emoji": "\ud83c\udf18",
            "zodiac": {
                "sun_sign": "Gem",
                "moon_sign": "Ari"
            },
            "moonrise": null,
            "moonrise_timestamp": null,
            "moonset": null,
            "moonset_timestamp": null,
            "next_lunar_eclipse": {
                "timestamp": 1726627457,
                "datestamp": "Wed, 18 Sep 2024 02:44:17 +0000",
                "type": "Partial Lunar Eclipse",
                "visibility_regions": null
            },
            "detailed": {
                "position": null,
                "visibility": null,
                "upcoming_phases": {
                    "new_moon": {
                        "last": { "timestamp": 1716472388, "datestamp": "Thu, 23 May 2024 13:53:08 +0000", "days_ago": 9, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 1717677462, "datestamp": "Thu, 06 Jun 2024 12:37:42 +0000", "days_ago": null, "days_ahead": 5, "name": null, "description": null }
                    },
                    "first_quarter": {
                        "last": { "timestamp": 1717089160, "datestamp": "Thu, 30 May 2024 17:12:40 +0000", "days_ago": 2, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 1718342307, "datestamp": "Fri, 14 Jun 2024 05:18:27 +0000", "days_ago": null, "days_ahead": 13, "name": null, "description": null }
                    },
                    "full_moon": {
                        "last": { "timestamp": 1715138518, "datestamp": "Wed, 08 May 2024 03:21:58 +0000", "days_ago": 24, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 1719018473, "datestamp": "Sat, 22 Jun 2024 01:07:53 +0000", "days_ago": null, "days_ahead": 21, "name": null, "description": null }
                    },
                    "last_quarter": {
                        "last": { "timestamp": 1715773680, "datestamp": "Wed, 15 May 2024 11:48:00 +0000", "days_ago": 17, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 1719611604, "datestamp": "Fri, 28 Jun 2024 21:53:24 +0000", "days_ago": null, "days_ahead": 27, "name": null, "description": null }
                    }
                },
                "illumination_details": {
                    "percentage": 30.0,
                    "visible_fraction": 0.2978,
                    "phase_angle": 293.86
                }
            },
            "events": null
        },
        "location": {
            "latitude": "51",
            "longitude": "0",
            "precision": 0,
            "using_default_location": true,
            "note": null
        }
    }
}
```

The `context` field contains an XML representation of the moon phase overview, optimized for AI/LLM consumption. The exact values will vary depending on the current UTC time. The response structure is always the same as `/api/v5/moon-phase/context`.
