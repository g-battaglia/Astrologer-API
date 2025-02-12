# Astrologer API

The Astrologer API is a RESTful service providing extensive astrology calculations, designed for seamless integration into your projects. It offers a rich set of astrological data and insights, making it an invaluable tool for both developers and astrology enthusiasts.

## Subscription

To access the Astrologer API, subscribe here:

[Subscribe to Astrologer API](https://rapidapi.com/gbattaglia/api/astrologer/pricing)

## Documentation

Explore the comprehensive API documentation with interactive features:

[Astrologer API OpenAPI (Swagger) Documentation](https://www.kerykeion.net/astrologer-api-swagger/)

## Getting Started

To begin using the Astrologer API, include your API key in the request headers. This key is essential for authenticating your requests and ensuring they are processed correctly.

### Example Request Headers

Ensure your API requests include the following headers:

```javascript
headers: {
    'X-RapidAPI-Host': 'astrologer.p.rapidapi.com',
    'X-RapidAPI-Key': 'YOUR_API_KEY'
    }
```

Replace `YOUR_API_KEY` with your actual API key obtained during registration.

## Features

### Charts

The Astrologer API provides various `*-chart` endpoints with customizable options:

#### Languages

You can specify the `lang` parameter to select the language for your chart. Available options are:

- `EN`: English (default)
- `FR`: French
- `PT`: Portuguese
- `ES`: Spanish
- `TR`: Turkish
- `RU`: Russian
- `IT`: Italian
- `CN`: Chinese
- `DE`: German
- `HI`: Hindi

Example API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Tropic"
    },
    "language": "RU"
}
```

#### Themes

Customize the appearance of your charts using the `theme` parameter. Available themes include:

- `classic`: A traditional, colorful theme
- `light`: A modern, soft-colored light theme
- `dark`: A modern dark theme
- `dark-high-contrast`: A dark theme with enhanced contrast for better readability

Example API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Tropic"
    },
    "theme": "dark"
}
```

### Zodiac Types

You can choose between the Sidereal and Tropical zodiacs using the `zodiac_type` parameter in the `subject` key of most endpoints.

- `tropic`: Tropical zodiac (default)
- `sidereal`: Sidereal zodiac

If you select `sidereal`, you must also specify the `sidereal_mode` parameter, which offers various ayanamsha (zodiacal calculation modes):

- `FAGAN_BRADLEY`
- `LAHIRI` (standard for Vedic astrology)
- `DELUCE`
- `RAMAN`
- `USHASHASHI`
- `KRISHNAMURTI`
- `DJWHAL_KHUL`
- `YUKTESHWAR`
- `JN_BHASIN`
- `BABYL_KUGLER1`
- `BABYL_KUGLER2`
- `BABYL_KUGLER3`
- `BABYL_HUBER`
- `BABYL_ETPSC`
- `ALDEBARAN_15TAU`
- `HIPPARCHOS`
- `SASSANIAN`
- `J2000`
- `J1900`
- `B1950`

The most commonly used ayanamshas are `FAGAN_BRADLEY` and `LAHIRI`.

Example API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Sidereal",
        "sidereal_mode": "FAGAN_BRADLEY"
    }
}
```

### House Systems

The `HouseSystem` parameter defines the method used to divide the celestial sphere into twelve houses. Here are the available options:

- **A**: Equal
- **B**: Alcabitius
- **C**: Campanus
- **D**: Equal (MC)
- **F**: Carter poli-equ.
- **H**: Horizon/Azimut
- **I**: Sunshine
- **i**: Sunshine/Alt.
- **K**: Koch
- **L**: Pullen SD
- **M**: Morinus
- **N**: Equal/1=Aries
- **O**: Porphyry
- **P**: Placidus
- **Q**: Pullen SR
- **R**: Regiomontanus
- **S**: Sripati
- **T**: Polich/Page
- **U**: Krusinski-Pisa-Goelzer
- **V**: Equal/Vehlow
- **W**: Equal/Whole Sign
- **X**: Axial rotation system/Meridian houses
- **Y**: APC houses

Usually, the standard house system used is Placidus (P).

Example API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Tropic",
        "house_system": "A"
    }
}
```

This allows you to specify the desired house system for calculating and displaying the positions of celestial bodies.

### Perspective Types

The PerspectiveType defines the viewpoint from which the positions of celestial bodies are calculated. Here are the available options:

- "Apparent Geocentric": Earth-centered and shows the apparent positions of celestial bodies as seen from Earth. This is the most commonly used and the default perspective.
- "Heliocentric": Sun-centered.
- "Topocentric": This perspective is based on the observer's specific location on the Earth's surface.
- "True Geocentric": This perspective is also Earth-centered but shows the true positions of celestial bodies without the apparent shifts caused by Earth's atmosphere.
  
Usually, the standard perspective used is "Apparent Geocentric".

Example usage in an API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Tropic",
        "perspective": "Heliocentric"
    }
}
```

This allows you to specify the desired perspective for calculating and displaying the positions of celestial bodies.

### Wheel Only Charts

To generate charts that contain only the zodiac wheel without any textual information, you can use the `wheel_only` option in your API call. When this option is set to `True`, only the zodiac wheel will be returned.

Example API request:

```json
{
    "subject": {
        "year": 1980,
        "month": 12,
        "day": 12,
        "hour": 12,
        "minute": 12,
        "longitude": 0,
        "latitude": 51.4825766,
        "city": "London",
        "nation": "GB",
        "timezone": "Europe/London",
        "name": "John Doe",
        "zodiac_type": "Tropic"
    },
    "wheel_only": true
}
```

This can be useful for creating clean and simple visual representations of the zodiac without any additional clutter.

## Timezones

Accurate astrological calculations require the correct timezone. Refer to the following link for a complete list of timezones:

[List of TZ Database Time Zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## Copyright and License

Astrologer API is Free/Libre Open Source Software with an AGPLv3 license. All the terms and conditions of the AGPLv3 license apply to the Astrologer API.
You can review and contribute to the source code via the official repositories:

- [V4 Astrologer API](https://github.com/g-battaglia/v4.astrologer-api)
- [V3 Astrologer API](https://github.com/g-battaglia/Astrologer-API)

Astrologer API is developed by Giacomo Battaglia and is based on Kerykeion, a Python library for astrology calculations by the same author. The underlying tools are built on the Swiss Ephemeris.

Since it is an external API service, integrating data and charts retrieved via the API does not impose any licensing restrictions, allowing use in projects with closed source licenses.

## Commercial Use

The Astrologer API can be freely used in both open-source and closed-source commercial applications without restrictions, as it functions as an external service.

For full compliance, we recommend adding this statement in your Terms and Conditions or elsewhere on your site/app:

---
---
Astrological data and charts on this site are generated using [AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer), an open-source third-party service licensed under AGPL v3. Source code:
- [V4 Astrologer API](https://github.com/g-battaglia/v4.astrologer-api)
- [V3 Astrologer API](https://github.com/g-battaglia/Astrologer-API)
---
---

This guarantees full transparency and complete licensing compliance, leaving no room for doubt.
