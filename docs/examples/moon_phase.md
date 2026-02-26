---
title: 'Moon Phase JSON Example'
description: 'Complete JSON example of detailed moon phase data including illumination, upcoming phases, eclipses, and sun position.'
---

# Moon Phase Example

Endpoint: `/api/v5/moon-phase`

## Request Body
```json
{
  "year": 1993,
  "month": 10,
  "day": 10,
  "hour": 12,
  "minute": 12,
  "second": 0,
  "latitude": 51.5074,
  "longitude": -0.1278,
  "timezone": "Europe/London"
}
```

## Response Body
```json
{
  "status": "OK",
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
        "altitude": 31.25357648244777,
        "azimuth": 169.66688621906792,
        "distance": 149364727.19422686
      },
      "next_solar_eclipse": {
        "timestamp": 753227093,
        "datestamp": "Sat, 13 Nov 1993 21:44:53 +0000",
        "type": "Partial Solar Eclipse",
        "visibility_regions": null
      }
    },
    "moon": {
      "phase": 0.8073589069399721,
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
            "last": {
              "timestamp": 749415231,
              "datestamp": "Thu, 30 Sep 1993 18:53:51 +0000",
              "days_ago": 10,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 750684955,
              "datestamp": "Fri, 15 Oct 1993 11:35:55 +0000",
              "days_ago": null,
              "days_ahead": 5,
              "name": null,
              "description": null
            }
          },
          "first_quarter": {
            "last": {
              "timestamp": 750108919,
              "datestamp": "Fri, 08 Oct 1993 19:35:19 +0000",
              "days_ago": 2,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 751279921,
              "datestamp": "Fri, 22 Oct 1993 08:52:01 +0000",
              "days_ago": null,
              "days_ahead": 12,
              "name": null,
              "description": null
            }
          },
          "full_moon": {
            "last": {
              "timestamp": 748149015,
              "datestamp": "Thu, 16 Sep 1993 03:10:15 +0000",
              "days_ago": 24,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 751984658,
              "datestamp": "Sat, 30 Oct 1993 12:37:38 +0000",
              "days_ago": null,
              "days_ahead": 20,
              "name": null,
              "description": null
            }
          },
          "last_quarter": {
            "last": {
              "timestamp": 748726326,
              "datestamp": "Wed, 22 Sep 1993 19:32:06 +0000",
              "days_ago": 18,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 752654150,
              "datestamp": "Sun, 07 Nov 1993 06:35:50 +0000",
              "days_ago": null,
              "days_ahead": 28,
              "name": null,
              "description": null
            }
          }
        },
        "illumination_details": {
          "percentage": 32.0,
          "visible_fraction": 0.3236772895463642,
          "phase_angle": 290.64920649838996
        }
      },
      "events": null
    },
    "location": {
      "latitude": "52",
      "longitude": "0",
      "precision": 0,
      "using_default_location": false,
      "note": null
    }
  }
}
```
