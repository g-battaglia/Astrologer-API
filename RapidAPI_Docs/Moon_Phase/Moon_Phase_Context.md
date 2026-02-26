## Endpoint
/api/v5/moon-phase/context

## Name

Moon Phase - AI Context

## Description

Returns detailed moon phase information with an AI-optimized XML context string, suitable for LLM consumption. This is the context variant of `/api/v5/moon-phase`.

This endpoint uses a simplified request model — no `subject` wrapper needed. Only date/time and geographic coordinates are required.

### Parameters

-   `year` (integer, required): Year of the event (1-3000).
-   `month` (integer, required): Month of the event (1-12).
-   `day` (integer, required): Day of the event (1-31).
-   `hour` (integer, required): Hour of the event (0-23).
-   `minute` (integer, required): Minute of the event (0-59).
-   `second` (integer, optional): Seconds of the event (0-59, default: 0).
-   `latitude` (float, required): Latitude of the location (-90 to 90).
-   `longitude` (float, required): Longitude of the location (-180 to 180).
-   `timezone` (string, required): IANA timezone identifier.
-   `using_default_location` (boolean, optional): Metadata flag (default: false).
-   `location_precision` (integer, optional): Number of decimal places used to round latitude and longitude in the response (0-10, default: 0). Display rounding only — calculations use full-precision coordinates.

## Request Body Example

```json
{
    "year": 1993,
    "month": 10,
    "day": 10,
    "hour": 12,
    "minute": 12,
    "latitude": 51.5074,
    "longitude": -0.1276,
    "timezone": "Europe/London",
    "location_precision": 4
}
```

## Response Body Example

```json
{
    "status": "OK",
    "context": "<moon_phase_overview timestamp=\"750251520\" datestamp=\"Sun, 10 Oct 1993 11:12:00 +0000\">...</moon_phase_overview>",
    "moon_phase_overview": {
        "timestamp": 750251520,
        "datestamp": "Sun, 10 Oct 1993 11:12:00 +0000",
        "sun": {
            "sunrise": 750233758,
            "sunrise_timestamp": "07:15",
            "sunset": 750273488,
            "sunset_timestamp": "18:18",
            "solar_noon": "12:47",
            "day_length": "11:02",
            "position": {
                "altitude": 31.25,
                "azimuth": 169.67,
                "distance": 149364727.19
            },
            "next_solar_eclipse": {
                "timestamp": 753227093,
                "datestamp": "Sat, 13 Nov 1993 21:44:53 +0000",
                "type": "Partial Solar Eclipse",
                "visibility_regions": null
            }
        },
        "moon": {
            "phase": 0.807,
            "phase_name": "Waning Crescent",
            "major_phase": "Last Quarter",
            "stage": "waning",
            "illumination": "32%",
            "age_days": 10,
            "lunar_cycle": "80.736%",
            "emoji": "\ud83c\udf18",
            "zodiac": {
                "sun_sign": "Lib",
                "moon_sign": "Leo"
            },
            "moonrise": null,
            "moonrise_timestamp": null,
            "moonset": null,
            "moonset_timestamp": null,
            "next_lunar_eclipse": {
                "timestamp": 754554366,
                "datestamp": "Mon, 29 Nov 1993 06:26:06 +0000",
                "type": "Total Lunar Eclipse",
                "visibility_regions": null
            },
            "detailed": {
                "position": null,
                "visibility": null,
                "upcoming_phases": {
                    "new_moon": {
                        "last": { "timestamp": 749415231, "datestamp": "Thu, 30 Sep 1993 18:53:51 +0000", "days_ago": 10, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 750684955, "datestamp": "Fri, 15 Oct 1993 11:35:55 +0000", "days_ago": null, "days_ahead": 5, "name": null, "description": null }
                    },
                    "first_quarter": {
                        "last": { "timestamp": 750108919, "datestamp": "Fri, 08 Oct 1993 19:35:19 +0000", "days_ago": 2, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 751279921, "datestamp": "Fri, 22 Oct 1993 08:52:01 +0000", "days_ago": null, "days_ahead": 12, "name": null, "description": null }
                    },
                    "full_moon": {
                        "last": { "timestamp": 748149015, "datestamp": "Thu, 16 Sep 1993 03:10:15 +0000", "days_ago": 24, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 751984658, "datestamp": "Sat, 30 Oct 1993 12:37:38 +0000", "days_ago": null, "days_ahead": 20, "name": null, "description": null }
                    },
                    "last_quarter": {
                        "last": { "timestamp": 748726326, "datestamp": "Wed, 22 Sep 1993 19:32:06 +0000", "days_ago": 18, "days_ahead": null, "name": null, "description": null },
                        "next": { "timestamp": 752654150, "datestamp": "Sun, 07 Nov 1993 06:35:50 +0000", "days_ago": null, "days_ahead": 28, "name": null, "description": null }
                    }
                },
                "illumination_details": {
                    "percentage": 32.0,
                    "visible_fraction": 0.3237,
                    "phase_angle": 290.65
                }
            },
            "events": null
        },
        "location": {
            "latitude": "51.5074",
            "longitude": "-0.1276",
            "precision": 4,
            "using_default_location": false,
            "note": null
        }
    }
}
```

The `context` field contains an XML representation of the moon phase overview, optimized for AI/LLM consumption. The `moon_phase_overview` field contains the same data in JSON format.

Values are rounded for brevity. Fields that may be `null` (`moonrise`, `moonset`, `position`, `visibility`, `events`, `name`, `description`, `visibility_regions`, `note`) are reserved for future expansion.
