---
title: 'Moon Phase Now Context (UTC) JSON Example'
description: 'Complete JSON example of current moon phase data with AI-optimized XML context at Greenwich.'
---

# Moon Phase Now (UTC) Context Example

Endpoint: `/api/v5/moon-phase/now-utc/context`

## Request Body
```json
{}
```

## Response Body
```json
{
  "status": "OK",
  "context": "<moon_phase_overview timestamp=\"1773846747\" datestamp=\"Wed, 18 Mar 2026 15:12:27 +0000\">\n  <moon>\n    <phase>0.985</phase>\n    <phase_name>Waning Crescent</phase_name>\n    <major_phase>New Moon</major_phase>\n    <stage>waning</stage>\n    <illumination>0%</illumination>\n    <age_days>15</age_days>\n    <lunar_cycle>98.479%</lunar_cycle>\n    <emoji>\ud83c\udf18</emoji>\n    <zodiac sun_sign=\"Pis\" moon_sign=\"Pis\" />\n    <next_lunar_eclipse timestamp=\"1787890378\" datestamp=\"Fri, 28 Aug 2026 04:12:58 +0000\" type=\"Partial Lunar Eclipse\" />\n    <detailed>\n      <upcoming_phases>\n        <new_moon>\n          <last timestamp=\"1772537875\" datestamp=\"Tue, 03 Mar 2026 11:37:55 +0000\" days_ago=\"15\" />\n          <next timestamp=\"1776426709\" datestamp=\"Fri, 17 Apr 2026 11:51:49 +0000\" days_ahead=\"30\" />\n        </new_moon>\n        <first_quarter>\n          <last timestamp=\"1773221910\" datestamp=\"Wed, 11 Mar 2026 09:38:30 +0000\" days_ago=\"7\" />\n          <next timestamp=\"1774466263\" datestamp=\"Wed, 25 Mar 2026 19:17:43 +0000\" days_ahead=\"7\" />\n        </first_quarter>\n        <full_moon>\n          <last timestamp=\"1773846746\" datestamp=\"Wed, 18 Mar 2026 15:12:26 +0000\" days_ago=\"0\" />\n          <next timestamp=\"1775095919\" datestamp=\"Thu, 02 Apr 2026 02:11:59 +0000\" days_ahead=\"14\" />\n        </full_moon>\n        <last_quarter>\n          <last timestamp=\"1771936055\" datestamp=\"Tue, 24 Feb 2026 12:27:35 +0000\" days_ago=\"22\" />\n          <next timestamp=\"1775796700\" datestamp=\"Fri, 10 Apr 2026 04:51:40 +0000\" days_ahead=\"23\" />\n        </last_quarter>\n      </upcoming_phases>\n      <illumination_details percentage=\"0.0\" visible_fraction=\"0.0023\" phase_angle=\"354.52\" />\n    </detailed>\n  </moon>\n  <sun>\n    <sunrise>1773814049</sunrise>\n    <sunrise_timestamp>06:07</sunrise_timestamp>\n    <sunset>1773857373</sunset>\n    <sunset_timestamp>18:09</sunset_timestamp>\n    <solar_noon>12:08</solar_noon>\n    <day_length>12:02</day_length>\n    <position altitude=\"24.90\" azimuth=\"232.61\" distance=\"148905129.11\" />\n    <next_solar_eclipse timestamp=\"1786556757\" datestamp=\"Wed, 12 Aug 2026 17:45:57 +0000\" type=\"Total Solar Eclipse\" />\n  </sun>\n  <location latitude=\"51.477928\" longitude=\"-0.001545\" precision=\"0\" using_default_location=\"true\" />\n</moon_phase_overview>",
  "moon_phase_overview": {
    "timestamp": 1773846747,
    "datestamp": "Wed, 18 Mar 2026 15:12:27 +0000",
    "sun": {
      "sunrise": 1773814049,
      "sunrise_timestamp": "06:07",
      "sunset": 1773857373,
      "sunset_timestamp": "18:09",
      "solar_noon": "12:08",
      "day_length": "12:02",
      "position": {
        "altitude": 24.898407633291985,
        "azimuth": 232.6076450908489,
        "distance": 148905129.11008686
      },
      "next_solar_eclipse": {
        "timestamp": 1786556757,
        "datestamp": "Wed, 12 Aug 2026 17:45:57 +0000",
        "type": "Total Solar Eclipse",
        "visibility_regions": null
      }
    },
    "moon": {
      "phase": 0.9847884452581449,
      "phase_name": "Waning Crescent",
      "major_phase": "New Moon",
      "stage": "waning",
      "illumination": "0%",
      "age_days": 15,
      "lunar_cycle": "98.479%",
      "emoji": "\ud83c\udf18",
      "zodiac": {
        "sun_sign": "Pis",
        "moon_sign": "Pis"
      },
      "moonrise": null,
      "moonrise_timestamp": null,
      "moonset": null,
      "moonset_timestamp": null,
      "next_lunar_eclipse": {
        "timestamp": 1787890378,
        "datestamp": "Fri, 28 Aug 2026 04:12:58 +0000",
        "type": "Partial Lunar Eclipse",
        "visibility_regions": null
      },
      "detailed": {
        "position": null,
        "visibility": null,
        "upcoming_phases": {
          "new_moon": {
            "last": {
              "timestamp": 1772537875,
              "datestamp": "Tue, 03 Mar 2026 11:37:55 +0000",
              "days_ago": 15,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1776426709,
              "datestamp": "Fri, 17 Apr 2026 11:51:49 +0000",
              "days_ago": null,
              "days_ahead": 30,
              "name": null,
              "description": null
            }
          },
          "first_quarter": {
            "last": {
              "timestamp": 1773221910,
              "datestamp": "Wed, 11 Mar 2026 09:38:30 +0000",
              "days_ago": 7,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1774466263,
              "datestamp": "Wed, 25 Mar 2026 19:17:43 +0000",
              "days_ago": null,
              "days_ahead": 7,
              "name": null,
              "description": null
            }
          },
          "full_moon": {
            "last": {
              "timestamp": 1773846746,
              "datestamp": "Wed, 18 Mar 2026 15:12:26 +0000",
              "days_ago": 0,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1775095919,
              "datestamp": "Thu, 02 Apr 2026 02:11:59 +0000",
              "days_ago": null,
              "days_ahead": 14,
              "name": null,
              "description": null
            }
          },
          "last_quarter": {
            "last": {
              "timestamp": 1771936055,
              "datestamp": "Tue, 24 Feb 2026 12:27:35 +0000",
              "days_ago": 22,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1775796700,
              "datestamp": "Fri, 10 Apr 2026 04:51:40 +0000",
              "days_ago": null,
              "days_ahead": 23,
              "name": null,
              "description": null
            }
          }
        },
        "illumination_details": {
          "percentage": 0.0,
          "visible_fraction": 0.0022820035942130446,
          "phase_angle": 354.52384029293216
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
