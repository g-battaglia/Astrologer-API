"""
Test per gli endpoint moon phase v5.

Obiettivi:
- Caso base OK con data/ora/posizione validi.
- Verifica struttura response completa (moon, sun, location).
- Verifica valori noti per fasi lunari conosciute.
- Endpoint now-utc con body vuoto.
- Errore 422 su campi mancanti, extra fields, timezone invalido.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


# Londra, 10 Ottobre 1993 12:12 UTC - Waning Crescent
LONDON_MOON_PHASE_REQUEST = {
    "year": 1993,
    "month": 10,
    "day": 10,
    "hour": 12,
    "minute": 12,
    "second": 0,
    "latitude": 51.5074,
    "longitude": -0.1276,
    "timezone": "Europe/London",
}


# ---- Successo ----


def test_moon_phase_success(client: TestClient):
    """Test base: verifica struttura response completa."""
    resp = client.post("/api/v5/moon-phase", json=LONDON_MOON_PHASE_REQUEST)
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "OK"
    overview = body["moon_phase_overview"]

    # Top-level fields
    assert "timestamp" in overview
    assert "datestamp" in overview
    assert isinstance(overview["timestamp"], int)
    assert isinstance(overview["datestamp"], str)

    # Moon section
    moon = overview["moon"]
    assert moon is not None
    for key in (
        "phase",
        "phase_name",
        "major_phase",
        "stage",
        "illumination",
        "age_days",
        "lunar_cycle",
        "emoji",
    ):
        assert key in moon, f"Missing key: {key}"

    assert isinstance(moon["phase"], float)
    assert 0.0 <= moon["phase"] <= 1.0
    assert moon["stage"] in ("waxing", "waning")
    assert moon["phase_name"] in (
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    )

    # Zodiac info
    zodiac = moon["zodiac"]
    assert zodiac is not None
    assert "sun_sign" in zodiac
    assert "moon_sign" in zodiac

    # Detailed section
    detailed = moon["detailed"]
    assert detailed is not None

    # Upcoming phases
    upcoming = detailed["upcoming_phases"]
    assert upcoming is not None
    for phase_key in ("new_moon", "first_quarter", "full_moon", "last_quarter"):
        assert phase_key in upcoming
        phase_window = upcoming[phase_key]
        assert "last" in phase_window
        assert "next" in phase_window

    # Illumination details
    illum = detailed["illumination_details"]
    assert illum is not None
    assert "percentage" in illum
    assert "visible_fraction" in illum
    assert "phase_angle" in illum

    # Sun section
    sun = overview["sun"]
    assert sun is not None

    # Location section
    location = overview["location"]
    assert location is not None
    assert "latitude" in location
    assert "longitude" in location


def test_moon_phase_known_values_waning_crescent(client: TestClient):
    """Verifica valori noti: 10 Ottobre 1993 era Waning Crescent."""
    resp = client.post("/api/v5/moon-phase", json=LONDON_MOON_PHASE_REQUEST)
    assert resp.status_code == 200
    moon = resp.json()["moon_phase_overview"]["moon"]

    assert moon["phase_name"] == "Waning Crescent"
    assert moon["stage"] == "waning"
    assert moon["emoji"] == "\U0001f318"  # 🌘
    assert moon["zodiac"]["sun_sign"] == "Lib"
    assert moon["zodiac"]["moon_sign"] == "Leo"


def test_moon_phase_known_values_full_moon(client: TestClient):
    """Verifica valori noti: 28 Ottobre 2023 20:24 UTC era Full Moon (Hunter's Moon)."""
    resp = client.post(
        "/api/v5/moon-phase",
        json={
            "year": 2023,
            "month": 10,
            "day": 28,
            "hour": 20,
            "minute": 24,
            "latitude": 51.5074,
            "longitude": -0.1276,
            "timezone": "Etc/UTC",
        },
    )
    assert resp.status_code == 200
    moon = resp.json()["moon_phase_overview"]["moon"]

    assert moon["phase_name"] == "Full Moon"
    assert moon["emoji"] == "\U0001f315"  # 🌕


def test_moon_phase_known_values_new_moon(client: TestClient):
    """Verifica valori noti: 14 Ottobre 2023 18:00 UTC era New Moon (eclissi solare anulare)."""
    resp = client.post(
        "/api/v5/moon-phase",
        json={
            "year": 2023,
            "month": 10,
            "day": 14,
            "hour": 18,
            "minute": 0,
            "latitude": 51.5074,
            "longitude": -0.1276,
            "timezone": "Etc/UTC",
        },
    )
    assert resp.status_code == 200
    moon = resp.json()["moon_phase_overview"]["moon"]

    assert moon["phase_name"] == "New Moon"
    assert moon["emoji"] == "\U0001f311"  # 🌑


def test_moon_phase_without_optional_second(client: TestClient):
    """Test che il campo second sia opzionale (default 0)."""
    payload = {
        "year": 1993,
        "month": 10,
        "day": 10,
        "hour": 12,
        "minute": 12,
        "latitude": 51.5074,
        "longitude": -0.1276,
        "timezone": "Europe/London",
    }
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"


def test_moon_phase_with_location_precision(client: TestClient):
    """Test che location_precision arrotondi effettivamente le coordinate."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "location_precision": 4}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["precision"] == 4
    assert location["latitude"] == "51.5074"
    assert location["longitude"] == "-0.1276"


def test_moon_phase_precision_zero_rounds_to_integer(client: TestClient):
    """Con precision=0, le coordinate devono essere interi stringa."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "location_precision": 0}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["precision"] == 0
    # 51.5074 arrotondato a 0 decimali = 52
    assert location["latitude"] == "52"
    # -0.1276 arrotondato a 0 decimali = 0 (no segno negativo)
    assert location["longitude"] == "0"


def test_moon_phase_precision_default_is_zero(client: TestClient):
    """Senza specificare location_precision, default=0 e coordinate intere."""
    resp = client.post("/api/v5/moon-phase", json=LONDON_MOON_PHASE_REQUEST)
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["precision"] == 0
    assert location["latitude"] == "52"
    assert location["longitude"] == "0"


def test_moon_phase_precision_no_negative_zero(client: TestClient):
    """Coordinate vicine a zero non devono produrre '-0'."""
    payload = {
        "year": 2024,
        "month": 6,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "latitude": 0.004,
        "longitude": -0.004,
        "timezone": "Etc/UTC",
        "location_precision": 0,
    }
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["latitude"] == "0"
    assert location["longitude"] == "0"


def test_moon_phase_with_using_default_location(client: TestClient):
    """Test che using_default_location venga passato correttamente."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "using_default_location": True}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["using_default_location"] is True


def test_moon_phase_eclipse_fields_present(client: TestClient):
    """Verifica che i campi eclissi siano presenti nella response."""
    resp = client.post("/api/v5/moon-phase", json=LONDON_MOON_PHASE_REQUEST)
    assert resp.status_code == 200
    overview = resp.json()["moon_phase_overview"]

    # Next lunar eclipse
    lunar_eclipse = overview["moon"]["next_lunar_eclipse"]
    assert lunar_eclipse is not None
    assert "timestamp" in lunar_eclipse
    assert "type" in lunar_eclipse

    # Next solar eclipse
    sun = overview["sun"]
    assert "next_solar_eclipse" in sun
    solar_eclipse = sun["next_solar_eclipse"]
    assert solar_eclipse is not None
    assert "timestamp" in solar_eclipse
    assert "type" in solar_eclipse


# ---- Endpoint now-utc ----


def test_now_utc_moon_phase_empty_body(client: TestClient):
    """Test now-utc con body vuoto."""
    resp = client.post("/api/v5/moon-phase/now-utc", json={})
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "OK"
    overview = body["moon_phase_overview"]
    assert "moon" in overview
    assert "sun" in overview
    assert "location" in overview

    # Deve usare le coordinate di Greenwich
    location = overview["location"]
    assert location["using_default_location"] is True


def test_now_utc_moon_phase_frozen_time(client: TestClient):
    """Verifica che now-utc usi il tempo congelato dal conftest (2024-06-01 12:30 UTC)."""
    resp = client.post("/api/v5/moon-phase/now-utc", json={})
    assert resp.status_code == 200
    overview = resp.json()["moon_phase_overview"]

    # Il datestamp deve contenere "01 Jun 2024" (il tempo congelato)
    assert "01 Jun 2024" in overview["datestamp"]


def test_now_utc_moon_phase_custom_precision(client: TestClient):
    """Test now-utc con location_precision personalizzato."""
    resp = client.post("/api/v5/moon-phase/now-utc", json={"location_precision": 4})
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["precision"] == 4
    # Greenwich coords (51.477928, -0.001545) arrotondate a 4 decimali
    assert location["latitude"] == "51.4779"
    assert location["longitude"] == "-0.0015"


def test_now_utc_moon_phase_default_precision(client: TestClient):
    """Test now-utc con precision default=0: coordinate intere, no -0."""
    resp = client.post("/api/v5/moon-phase/now-utc", json={})
    assert resp.status_code == 200
    location = resp.json()["moon_phase_overview"]["location"]
    assert location["precision"] == 0
    # Greenwich 51.477928 -> 51, -0.001545 -> 0 (no -0)
    assert location["latitude"] == "51"
    assert location["longitude"] == "0"


# ---- Context endpoints ----


def test_moon_phase_context(client: TestClient):
    """Test /api/v5/moon-phase/context endpoint."""
    payload = {
        "year": 1993,
        "month": 10,
        "day": 10,
        "hour": 12,
        "minute": 12,
        "latitude": 51.5074,
        "longitude": -0.1276,
        "timezone": "Europe/London",
    }
    resp = client.post("/api/v5/moon-phase/context", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context (XML format)
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0
    assert "<moon_phase_overview" in body["context"]

    # Verifica presenza moon_phase_overview
    assert "moon_phase_overview" in body
    overview = body["moon_phase_overview"]
    assert "moon" in overview
    assert "sun" in overview
    assert "location" in overview

    # Verifica ordine campi (context prima di moon_phase_overview)
    keys = list(body.keys())
    assert keys.index("context") < keys.index("moon_phase_overview")

    # Verifica coerenza dati
    assert overview["moon"]["phase_name"] == "Waning Crescent"


def test_moon_phase_now_utc_context(client: TestClient):
    """Test /api/v5/moon-phase/now-utc/context endpoint."""
    resp = client.post("/api/v5/moon-phase/now-utc/context", json={})
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context (XML format)
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0
    assert "<moon_phase_overview" in body["context"]

    # Verifica presenza moon_phase_overview
    assert "moon_phase_overview" in body
    overview = body["moon_phase_overview"]
    assert "moon" in overview
    assert "sun" in overview

    # Deve usare le coordinate di Greenwich
    location = overview["location"]
    assert location["using_default_location"] is True

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("context") < keys.index("moon_phase_overview")


def test_moon_phase_context_with_precision(client: TestClient):
    """Test che location_precision venga rispettato anche nell'endpoint context."""
    payload = {
        "year": 1993,
        "month": 10,
        "day": 10,
        "hour": 12,
        "minute": 12,
        "latitude": 51.5074,
        "longitude": -0.1276,
        "timezone": "Europe/London",
        "location_precision": 4,
    }
    resp = client.post("/api/v5/moon-phase/context", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    location = body["moon_phase_overview"]["location"]
    assert location["precision"] == 4
    assert location["latitude"] == "51.5074"
    assert location["longitude"] == "-0.1276"


# ---- Validazione errori ----


def test_moon_phase_missing_required_fields(client: TestClient):
    """422 quando mancano campi obbligatori."""
    # Nessun campo: mancano year, month, day, hour, minute, latitude, longitude, timezone
    resp = client.post("/api/v5/moon-phase", json={})
    assert resp.status_code == 422


def test_moon_phase_missing_latitude(client: TestClient):
    """422 quando manca latitude."""
    payload = {**LONDON_MOON_PHASE_REQUEST}
    del payload["latitude"]
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_moon_phase_missing_timezone(client: TestClient):
    """422 quando manca timezone."""
    payload = {**LONDON_MOON_PHASE_REQUEST}
    del payload["timezone"]
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_moon_phase_invalid_timezone(client: TestClient):
    """422 con timezone invalido."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "timezone": "Invalid/Timezone"}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_moon_phase_extra_fields_rejected(client: TestClient):
    """422 su campi extra non previsti."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "name": "Should not be here"}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_moon_phase_extra_fields_rejected_city(client: TestClient):
    """422 su campo city (non previsto nel model semplificato)."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "city": "London"}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_now_utc_moon_phase_extra_fields_rejected(client: TestClient):
    """422 su campi extra per endpoint now-utc."""
    resp = client.post("/api/v5/moon-phase/now-utc", json={"year": 2024})
    assert resp.status_code == 422


def test_moon_phase_latitude_out_of_range(client: TestClient):
    """422 con latitude fuori range."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "latitude": 91.0}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_moon_phase_longitude_out_of_range(client: TestClient):
    """422 con longitude fuori range."""
    payload = {**LONDON_MOON_PHASE_REQUEST, "longitude": 181.0}
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422
