"""
Test per gli endpoint `now/*` (soggetto e chart).

Scelte di test:
- Verifica che il soggetto si chiami "Now" e che il timestamp sia quello congelato.
- Verifica che la chart SVG venga generata e che i dati abbiano una forma coerente.
- Verifica che la chart supporti le opzioni di rendering (split_chart, theme, etc.) via POST.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import assert_api_svg_valid


def test_now_subject(client: TestClient):
    """Test default behavior (POST with empty body)."""
    resp = client.post("/api/v5/now/subject", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "OK"
    subject = body["subject"]
    assert subject["name"] == "Now"
    # Il conftest congela l'orario, l'ISO deve iniziare con quel valore
    assert subject["iso_formatted_utc_datetime"].startswith("2024-06-01T12:30:00+")


def test_now_subject_custom_config(client: TestClient):
    """Test custom configuration for now subject."""
    payload = {
        "name": "Custom Now",
        "zodiac_type": "Sidereal",
        "sidereal_mode": "LAHIRI",
        "houses_system_identifier": "W",
    }
    resp = client.post("/api/v5/now/subject", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    subject = body["subject"]
    assert subject["name"] == "Custom Now"
    assert subject["zodiac_type"] == "Sidereal"
    assert subject["sidereal_mode"] == "LAHIRI"
    assert subject["houses_system_identifier"] == "W"


def test_now_chart_default(client: TestClient):
    """Test default behavior (POST with empty body or defaults)."""
    resp = client.post("/api/v5/now/chart", json={})
    assert resp.status_code == 200
    body = resp.json()

    # Chart SVG — full XML well-formedness + CSS variables check
    assert_api_svg_valid(body["chart"])
    assert "chart_wheel" not in body
    assert "chart_grid" not in body

    # Struttura minima dei dati coerente con un natal chart singolo
    data = body["chart_data"]
    assert data["chart_type"] == "Natal"
    assert "subject" in data
    assert isinstance(data["active_points"], list) and data["active_points"]
    assert isinstance(data["active_aspects"], list) and data["active_aspects"]
    assert data["element_distribution"]["air_percentage"] >= 0
    assert data["quality_distribution"]["mutable_percentage"] >= 0


def test_now_chart_split(client: TestClient):
    """Test split_chart=True returns separate SVGs."""
    payload = {"split_chart": True}
    resp = client.post("/api/v5/now/chart", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    assert "chart" not in body
    assert "chart_wheel" in body
    assert_api_svg_valid(body["chart_wheel"])
    assert "chart_grid" in body
    assert_api_svg_valid(body["chart_grid"])


def test_now_chart_custom_config(client: TestClient):
    """Test custom subject configuration in chart request."""
    payload = {
        "name": "Chart Now",
        "zodiac_type": "Sidereal",
        "sidereal_mode": "LAHIRI",
        "custom_title": "My Title",
    }
    resp = client.post("/api/v5/now/chart", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    # Check chart data reflects config
    data = body["chart_data"]
    assert data["subject"]["name"] == "Chart Now"
    assert data["subject"]["zodiac_type"] == "Sidereal"
    assert data["subject"]["sidereal_mode"] == "LAHIRI"

    # Check title in SVG (simple check)
    assert "My Title" in body["chart"]
