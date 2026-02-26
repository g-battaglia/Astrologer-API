"""
Test completi per gli endpoint context.

Obiettivi:
- Verificare che tutti gli 8 endpoint context rispondano correttamente (200).
- Verificare la presenza di context/subject_context.
- Verificare che context/subject_context siano stringhe non vuote.
- Verificare la presenza di chart_data/subject.
- Verificare l'ordine corretto dei campi (context prima di chart_data).
- Verificare la struttura dei dati restituiti.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

from fastapi.testclient import TestClient


BASE_SUBJECT: Dict[str, object] = {
    "name": "Context Test",
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "longitude": 12.4964,
    "latitude": 41.9028,
    "city": "Rome",
    "nation": "IT",
    "timezone": "Europe/Rome",
}

SECOND_SUBJECT: Dict[str, object] = {
    "name": "Context Test 2",
    "year": 1988,
    "month": 3,
    "day": 20,
    "hour": 10,
    "minute": 15,
    "longitude": 2.3522,
    "latitude": 48.8566,
    "city": "Paris",
    "nation": "FR",
    "timezone": "Europe/Paris",
}


def test_subject_context(client: TestClient):
    """Test /api/v5/context/subject endpoint."""
    resp = client.post(
        "/api/v5/context/subject", json={"subject": deepcopy(BASE_SUBJECT)}
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza subject_context
    assert "subject_context" in body
    assert isinstance(body["subject_context"], str)
    assert len(body["subject_context"]) > 0
    assert "<chart " in body["subject_context"]

    # Verifica presenza subject
    assert "subject" in body
    assert isinstance(body["subject"], dict)
    assert body["subject"]["name"] == "Context Test"

    # Verifica ordine campi (subject_context prima di subject)
    keys = list(body.keys())
    assert keys.index("subject_context") < keys.index("subject")


def test_subject_context_respects_active_points(client: TestClient):
    """Verifica che il parametro active_points venga correttamente applicato in context/subject."""
    custom_active_points = ["Sun", "Moon", "Ascendant", "Spica"]
    resp = client.post(
        "/api/v5/context/subject",
        json={
            "subject": deepcopy(BASE_SUBJECT),
            "active_points": custom_active_points,
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # active_points nel soggetto deve corrispondere a quelli richiesti
    # (l'ordine può variare perché Kerykeion riordina i punti internamente)
    assert set(body["subject"]["active_points"]) == set(custom_active_points)
    assert len(body["subject"]["active_points"]) == len(custom_active_points)


def test_now_context(client: TestClient):
    """Test /api/v5/now/context endpoint."""
    resp = client.post("/api/v5/now/context", json={"name": "Now Context Test"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza subject_context
    assert "subject_context" in body
    assert isinstance(body["subject_context"], str)
    assert len(body["subject_context"]) > 0

    # Verifica presenza subject
    assert "subject" in body
    assert isinstance(body["subject"], dict)

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("subject_context") < keys.index("subject")


def test_natal_context(client: TestClient):
    """Test /api/v5/context/birth-chart endpoint."""
    resp = client.post(
        "/api/v5/context/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0
    assert 'type="Natal"' in body["context"]

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    assert data["chart_type"] == "Natal"
    assert "subject" in data
    assert isinstance(data["aspects"], list)

    # Verifica ordine campi (context prima di chart_data)
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_synastry_context(client: TestClient):
    """Test /api/v5/context/synastry endpoint."""
    resp = client.post(
        "/api/v5/context/synastry",
        json={
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0
    assert "Synastry" in body["context"] or "First Subject" in body["context"]

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    assert data["chart_type"] == "Synastry"
    assert "first_subject" in data
    assert "second_subject" in data

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_composite_context(client: TestClient):
    """Test /api/v5/context/composite endpoint."""
    resp = client.post(
        "/api/v5/context/composite",
        json={
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    assert data["chart_type"] == "Composite"
    assert "subject" in data

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_transit_context(client: TestClient):
    """Test /api/v5/context/transit endpoint."""
    transit_subject = {
        "name": "Transit",
        "year": 2024,
        "month": 10,
        "day": 27,
        "hour": 12,
        "minute": 0,
        "city": "Rome",
        "nation": "IT",
        "longitude": 12.4964,
        "latitude": 41.9028,
        "timezone": "Europe/Rome",
    }

    resp = client.post(
        "/api/v5/context/transit",
        json={
            "first_subject": deepcopy(BASE_SUBJECT),
            "transit_subject": transit_subject,
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    assert data["chart_type"] == "Transit"
    assert "first_subject" in data
    assert "second_subject" in data

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_solar_return_context(client: TestClient):
    """Test /api/v5/context/solar-return endpoint."""
    resp = client.post(
        "/api/v5/context/solar-return",
        json={
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "dual",
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    assert data["chart_type"] == "DualReturnChart"

    # Verifica campi specifici dei return
    assert body["return_type"] == "Solar"
    assert body["wheel_type"] == "dual"

    # Verifica ordine campi (context prima di chart_data)
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_lunar_return_context(client: TestClient):
    """Test /api/v5/context/lunar-return endpoint."""
    resp = client.post(
        "/api/v5/context/lunar-return",
        json={
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "month": 6,
            "wheel_type": "single",
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "OK"

    # Verifica presenza context
    assert "context" in body
    assert isinstance(body["context"], str)
    assert len(body["context"]) > 0

    # Verifica presenza chart_data
    assert "chart_data" in body
    data = body["chart_data"]
    # Single wheel type restituisce SingleReturnChart
    assert data["chart_type"] in ["SingleReturnChart", "DualReturnChart"]

    # Verifica campi specifici dei return
    assert body["return_type"] == "Lunar"
    assert body["wheel_type"] == "single"

    # Verifica ordine campi
    keys = list(body.keys())
    assert keys.index("context") < keys.index("chart_data")


def test_context_content_quality(client: TestClient):
    """Test che il context contenga informazioni astrologiche rilevanti."""
    resp = client.post(
        "/api/v5/context/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
    )
    assert resp.status_code == 200

    context = resp.json()["context"]

    # Verifica che il context contenga elementi chiave
    assert "<chart_analysis" in context or "Natal" in context
    assert "1990" in context or "birth_data" in context

    # Verifica che contenga almeno alcuni pianeti
    planet_found = False
    for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
        if planet in context:
            planet_found = True
            break
    assert planet_found, "Context should mention at least one planet"

    # Verifica che contenga informazioni su segni zodiacali
    sign_found = False
    for sign in [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]:
        if sign in context:
            sign_found = True
            break
    assert sign_found, "Context should mention at least one zodiac sign"


def test_context_vs_chart_data_consistency(client: TestClient):
    """Test che i dati nel context siano coerenti con chart_data."""
    resp = client.post(
        "/api/v5/context/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
    )
    assert resp.status_code == 200

    body = resp.json()
    context = body["context"]
    chart_data = body["chart_data"]

    # Verifica che il nome del soggetto sia presente in entrambi
    subject_name = chart_data["subject"]["name"]
    assert subject_name in context

    # Verifica coerenza del tipo di chart
    if "Natal" in context or chart_data["chart_type"] == "Natal":
        assert chart_data["chart_type"] == "Natal"
