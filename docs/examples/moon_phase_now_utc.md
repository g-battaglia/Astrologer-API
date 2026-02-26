---
title: 'Moon Phase Now (UTC) JSON Example'
description: 'JSON example of real-time moon phase data at Greenwich Observatory. Shows the response structure for the current lunar state.'
---

# Moon Phase Now (UTC) Example

Endpoint: `/api/v5/moon-phase/now-utc`

## Request Body
```json
{}
```

## Response Body
```json
{
  "status": "OK",
  "moon_phase_overview": {
    "timestamp": 1772140847,
    "datestamp": "Thu, 26 Feb 2026 21:20:47 +0000",
    "sun": {
      "sunrise": 1772088701,
      "sunrise_timestamp": "06:51",
      "sunset": 1772127292,
      "sunset_timestamp": "17:34",
      "solar_noon": "12:13",
      "day_length": "10:43",
      "position": {
        "altitude": -34.44819401379985,
        "azimuth": 305.1105015529729,
        "distance": 148135276.1566846
      },
      "next_solar_eclipse": {
        "timestamp": 1786556757,
        "datestamp": "Wed, 12 Aug 2026 17:45:57 +0000",
        "type": "Total Solar Eclipse",
        "visibility_regions": null
      }
    },
    "moon": {
      "phase": 0.3368001069667679,
      "phase_name": "Waxing Gibbous",
      "major_phase": "First Quarter",
      "stage": "waxing",
      "illumination": "76%",
      "age_days": 25,
      "lunar_cycle": "33.68%",
      "emoji": "\ud83c\udf14",
      "zodiac": {
        "sun_sign": "Pis",
        "moon_sign": "Can"
      },
      "moonrise": null,
      "moonrise_timestamp": null,
      "moonset": null,
      "moonset_timestamp": null,
      "next_lunar_eclipse": {
        "timestamp": 1772537622,
        "datestamp": "Tue, 03 Mar 2026 11:33:42 +0000",
        "type": "Total Lunar Eclipse",
        "visibility_regions": null
      },
      "detailed": {
        "position": null,
        "visibility": null,
        "upcoming_phases": {
          "new_moon": {
            "last": {
              "timestamp": 1769983755,
              "datestamp": "Sun, 01 Feb 2026 22:09:15 +0000",
              "days_ago": 25,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1773883409,
              "datestamp": "Thu, 19 Mar 2026 01:23:29 +0000",
              "days_ago": null,
              "days_ahead": 20,
              "name": null,
              "description": null
            }
          },
          "first_quarter": {
            "last": {
              "timestamp": 1770640988,
              "datestamp": "Mon, 09 Feb 2026 12:43:08 +0000",
              "days_ago": 17,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1774466262,
              "datestamp": "Wed, 25 Mar 2026 19:17:42 +0000",
              "days_ago": null,
              "days_ahead": 27,
              "name": null,
              "description": null
            }
          },
          "full_moon": {
            "last": {
              "timestamp": 1771329669,
              "datestamp": "Tue, 17 Feb 2026 12:01:09 +0000",
              "days_ago": 9,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1772537875,
              "datestamp": "Tue, 03 Mar 2026 11:37:55 +0000",
              "days_ago": null,
              "days_ahead": 5,
              "name": null,
              "description": null
            }
          },
          "last_quarter": {
            "last": {
              "timestamp": 1771936056,
              "datestamp": "Tue, 24 Feb 2026 12:27:36 +0000",
              "days_ago": 2,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1773221910,
              "datestamp": "Wed, 11 Mar 2026 09:38:30 +0000",
              "days_ago": null,
              "days_ahead": 13,
              "name": null,
              "description": null
            }
          }
        },
        "illumination_details": {
          "percentage": 76.0,
          "visible_fraction": 0.7593719951910303,
          "phase_angle": 121.24803850803644
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
