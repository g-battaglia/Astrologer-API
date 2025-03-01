# Astrologer API

The Astrologer API is a comprehensive RESTful service for astrological calculations, ideal for seamless integration into applications and websites. Perfect for developers and astrology enthusiasts alike, it provides detailed charts and data for various astrological needs.

![John Lennon Chart Example](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart.svg)

## Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v4/birth-chart` | POST | Generates a SVG birth chart in string format. The body of the response includes the data for the subject and the aspects. |
| `/api/v4/synastry-chart` | POST | Generates a synastry chart for two subjects. The response includes the data for both subjects and the aspects between them and the SVG chart in string format
| `/api/v4/transit-chart` | POST | Generates a transit chart for a subject. The response includes the data for the subject and the aspects and the SVG chart in string format |
| `/api/v4/relationship-score` | POST | Calculates compatibility scores (0-44) using the Ciro Discepolo method |
| `/api/v4/natal-aspects-data` | POST | Returns birth chart data/aspects without the visual chart |
| `/api/v4/synastry-aspects-data` | POST | Provides synastry data/aspects without the visual chart |
| `/api/v4/birth-data` | POST | Returns basic birth chart data only, without the visual chart and aspects |
| `/api/v4/now` | GET | Delivers birth chart data only for current UTC time. No visual chart or aspects are included |

## Getting Started

### Subscription

Subscribe at: [Astrologer API on RapidAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing)

### Authentication

Include your API key in all requests:

```javascript
headers: {
    'X-RapidAPI-Host': 'astrologer.p.rapidapi.com',
    'X-RapidAPI-Key': 'YOUR_API_KEY'
}
```

### Documentation

- [Swagger Documentation](https://www.kerykeion.net/astrologer-api-swagger/)
- [Redoc Documentation](https://www.kerykeion.net/astrologer-api-redoc/)
- [OpenAPI Specification](https://raw.githubusercontent.com/g-battaglia/Astrologer-API/master/openapi.json)

## Feature Configuration

### Chart Customization

#### Active Points and Aspects

Customize which celestial bodies and aspects to include in your calculations:

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
    "active_points": [
        "Sun", "Moon", "Mercury", "Venus", "Mars", 
        "Jupiter", "Saturn", "Uranus", "Neptune", 
        "Pluto", "Mean_Node", "Chiron", "Ascendant", 
        "Medium_Coeli", "Mean_Lilith", "Mean_South_Node"
    ],
    "active_aspects": [
        { "name": "conjunction", "orb": 10 },
        { "name": "opposition", "orb": 10 },
        { "name": "trine", "orb": 8 },
        { "name": "sextile", "orb": 6 },
        { "name": "square", "orb": 5 },
        { "name": "quintile", "orb": 1 }
    ]
}
```

#### Language Options

Available languages:
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

Example:
```json
{
    "subject": { /* ... */ },
    "language": "IT"
}
```

#### Visual Themes

Available themes:

- `light`: Modern soft-colored light theme

![John Lennon Chart Example](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Light%20Theme%20-%20Natal%20Chart.svg)

- `dark`: Modern dark theme
  
![John Lennon Chart Example](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart.svg)

- `dark-high-contrast`: High-contrast dark theme

![John Lennon Chart Example](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Dark%20High%20Contrast%20Theme%20-%20Natal%20Chart.svg)

- `classic`: Traditional colorful theme

![Albert Einstein Chart Example](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/Albert%20Einstein%20-%20Natal%20Chart.svg)

Example:
```json
{
    "subject": { /* ... */ },
    "theme": "dark"
}
```

#### Wheel-Only Charts

Generate simplified chart visualizations:

```json
{
    "subject": { /* ... */ },
    "wheel_only": true
}
```

### Technical Configuration

#### Zodiac Types

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

Example:
```json
{
    "subject": {
        /* ... */
        "zodiac_type": "Sidereal",
        "sidereal_mode": "LAHIRI"
    }
}
```

#### House Systems

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

Example:
```json
{
    "subject": {
        /* ... */
        "house_system": "W"
    }
}
```

#### Perspective Types

Available perspectives:
- `Apparent Geocentric`: Earth-centered, apparent positions (default)
- `Heliocentric`: Sun-centered
- `Topocentric`: Based on observer's location
- `True Geocentric`: Earth-centered, true positions

Example:
```json
{
    "subject": {
        /* ... */
        "perspective": "Heliocentric"
    }
}
```

## Important Notes

### Timezones

For accurate calculations, use correct timezone identifiers from the [TZ Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

### License Information

- **License Type**: AGPLv3 (Free/Libre Open Source Software)
- **Source Code**: [V4 Astrologer API Repository](https://github.com/g-battaglia/v4.astrologer-api)

Since it is an external API service, integrating data and charts retrieved via the API does not impose any licensing restrictions, allowing use in projects with closed source licenses.

### Commercial Usage

The API can be used in both open and closed-source commercial projects without restrictions as it functions as an external service.

For full compliance, we recommend adding this statement in your Terms and Conditions or elsewhere on your site/app:

```
Astrological data and charts on this site are generated using AstrologerAPI, 
an open-source third-party service licensed under AGPL v3.
Source code: https://github.com/g-battaglia/Astrologer-API
```

## Contact & Support

Email: [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com)