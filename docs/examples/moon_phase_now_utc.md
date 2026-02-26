# Moon Phase Now (UTC) Example

Endpoint: `/api/v5/moon-phase/now-utc`

This example shows the current moon phase at Greenwich Observatory using the default empty request body.
Since this endpoint uses the current UTC time, the actual values in your response will differ from those shown here.

## Request Body
```json
{}
```

## Response Body
```json
{
  "status": "OK",
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
      "emoji": "🌘",
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
            "last": {
              "timestamp": 1716472388,
              "datestamp": "Thu, 23 May 2024 13:53:08 +0000",
              "days_ago": 9,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1717677462,
              "datestamp": "Thu, 06 Jun 2024 12:37:42 +0000",
              "days_ago": null,
              "days_ahead": 5,
              "name": null,
              "description": null
            }
          },
          "first_quarter": {
            "last": {
              "timestamp": 1717089160,
              "datestamp": "Thu, 30 May 2024 17:12:40 +0000",
              "days_ago": 2,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1718342307,
              "datestamp": "Fri, 14 Jun 2024 05:18:27 +0000",
              "days_ago": null,
              "days_ahead": 13,
              "name": null,
              "description": null
            }
          },
          "full_moon": {
            "last": {
              "timestamp": 1715138518,
              "datestamp": "Wed, 08 May 2024 03:21:58 +0000",
              "days_ago": 24,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1719018473,
              "datestamp": "Sat, 22 Jun 2024 01:07:53 +0000",
              "days_ago": null,
              "days_ahead": 21,
              "name": null,
              "description": null
            }
          },
          "last_quarter": {
            "last": {
              "timestamp": 1715773680,
              "datestamp": "Wed, 15 May 2024 11:48:00 +0000",
              "days_ago": 17,
              "days_ahead": null,
              "name": null,
              "description": null
            },
            "next": {
              "timestamp": 1719611604,
              "datestamp": "Fri, 28 Jun 2024 21:53:24 +0000",
              "days_ago": null,
              "days_ahead": 27,
              "name": null,
              "description": null
            }
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

### Notes

- **`location.latitude` / `location.longitude`**: Rounded to the number of decimal places specified by `location_precision` (default `0`, so integer strings). The actual coordinates used for calculation are Greenwich Observatory (51.4779°N, 0.0015°W). Set `location_precision` to a higher value (e.g., `4`) to see more decimal places.
- **`sunrise_timestamp` / `sunset_timestamp`**: Local time strings (HH:MM format), while `sunrise` / `sunset` are Unix timestamps (integers). The `_timestamp` suffix refers to the human-readable format, not a Unix timestamp.
- **Null fields** (`moonrise`, `moonset`, `position`, `visibility`, `events`, `name`, `description`, `visibility_regions`, `note`): These fields are reserved for future expansion or are only populated under specific conditions. Their presence in the response is guaranteed but their values may be `null`.
- **All times are in UTC** since this endpoint uses `Etc/UTC` as the timezone.
