# Astrologer API

Astrologer API is a RESTful API that provides access to astrology calculations.
The API is still in beta, so exhaustive documentation is still to be written.

**_Remeber_**:
Always include the API key in the request headers.

Example:

```json
 headers: {
    'X-RapidAPI-Host': 'astrologer.p.rapidapi.com',
    'X-RapidAPI-Key': 'YOUR_API_KEY'
  }
```

# Endpoints:

## Get Now:

URL: `https://astrologer.p.rapidapi.com/api/v2/now`

Method: `GET`

Parameters: None

Returns the current astrological data in the following format:

```json
{
  "name": "Now",
  "year": 2022,
  "month": 5,
  "day": 11,
  "hour": 0,
  "minute": 19,
  "city": "GMT",
  "nation": "UK",
  "lng": -0.001545,
  "lat": 51.477928,
  "tz_str": "GMT",
  "zodiac_type": "Tropic",
  "local_time": 0.31666666666666665,
  "utc_time": 0.31666666666666665,
  "julian_day": 2459710.5131944446,
  "sun": {
    "name": "Sun",
    "quality": "Fixed",
    "element": "Earth",
    "sign": "Tau",
    "sign_num": 1,
    "position": 20.31678553278155,
    "abs_pos": 50.31678553278155,
    "emoji": "♉️",
    "point_type": "Planet",
    "house": "Third House",
    "retrograde": false
  },
  ...
```

## Get Birthchart:

URL: https://astrologer.p.rapidapi.com/api/v2/birth-chart

Method: `POST`

Parameters to be insterted in the body:

-   `name` - The name of the person to get the birthchart for.
-   `year` - The year of birth.
-   `month` - The month of birth.
-   `day` - The day of birth.
-   `hour` - The hour of birth.
-   `minute` - The minute of birth.
-   `latitude` - The latitude of the birth location.
-   `longitude` - The longitude of the birth location.
-   `city` - The name of city of birth.
-   `timezone` - The timezone of the birth location.
-   `language` - The language of the birth chart, currently just English, Italian and Portuguese are available.

Returns the birthchart of a subject in SVG format. Also includes the birthchart data and aspects in the following JSON format:

```json
{
  chart:
  "<?xml version="1.0" encoding="UTF-8"?> ...",
  aspects: [
    {
      "p1_name":"Sun"
      "p1_abs_pos":196.80745447441493
      "p2_name":"Mercury"
      "p2_abs_pos":188.14294949505657
      "aspect":"conjunction"
      "orbit":8.664504979358355
      "aspect_degrees":0
      "color":"#5757e2"
      "aid":0
      "diff":8.664504979358355
      "p1":0
      "p2":2
    },
    ...
],
  data: {
    "name": "Peter",
    "year": 2022,
    "month": 5,
    "day": 11,
    "hour": 0,
    "minute": 19,
    "city": "GMT",
    "nation": "UK",
    "lng": -0.001545,
    "lat": 51.477928,
    "tz_str": "GMT",
    "zodiac_type": "Tropic",
    "local_time": 0.31666666666666665,
    "utc_time": 0.31666666666666665,
    "julian_day": 2459710.5131944446,
    "sun": {
      "name": "Sun",
      "quality": "Fixed",
      "element": "Earth",
      "sign": "Tau",
      "sign_num": 1,
      "position": 20.31678553278155,
      "abs_pos": 50.31678553278155,
      "emoji": "♉️",
      "point_type": "Planet",
      "house": "Third House",
      "retrograde": false
    },
  ...
```

# Timezones:

Here a list of all the timezones:
https://gist.github.com/astrologiadavvero/0fd43d6970a9b63af41659ea78b885e9

# Copyright

Astrologer API is a project by Giacomo Battaglia, it's based on Kerykeion, which is from the same author and is a Python library for astrology calculations. All the tools underneath are built upon the Swiss Ephemeris and must preserve the copyright of the Swiss Ephemeris and the AGPL license.

Authors of the Swiss Ephemeris: Dieter Koch and Alois Treindl (Astrodienst AG, Zuerich)
