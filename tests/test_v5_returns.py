"""
Test espliciti per ritorni planetari (solar e lunar) nelle varianti dual e single wheel.

Linee guida:
- Controllare "chart_type" coerente con la ruota richiesta.
- Verificare presence/assenza di house comparison a seconda della ruota.
- Verificare i metadati specifici degli endpoint `charts/*`: `return_type` e `wheel_type`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

from fastapi.testclient import TestClient

from tests.conftest import assert_api_svg_valid


BASE_SUBJECT: Dict[str, object] = {
    "name": "FastAPI Unit Test",
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
}


def test_solar_return_dual_chart_data(client: TestClient):
    payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "wheel_type": "dual"}
    resp = client.post("/api/v5/chart-data/solar-return", json=payload)
    assert resp.status_code == 200
    data = resp.json()["chart_data"]

    assert data["chart_type"] == "DualReturnChart"
    # Nelle dual wheel il soggetto di ritorno è il secondo
    assert data["second_subject"]["return_type"] == "Solar"
    assert data.get("house_comparison") not in (None, [], {})


def test_solar_return_dual_chart_svg(client: TestClient):
    payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "wheel_type": "dual"}
    resp = client.post("/api/v5/chart/solar-return", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert_api_svg_valid(body["chart"])
    assert body["return_type"] == "Solar"
    assert body["wheel_type"] == "dual"
    assert body["chart_data"]["chart_type"] == "DualReturnChart"


def test_lunar_return_single_chart_data(client: TestClient):
    payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "wheel_type": "single"}
    resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
    assert resp.status_code == 200
    data = resp.json()["chart_data"]

    assert data["chart_type"] == "SingleReturnChart"
    assert data["subject"]["return_type"] == "Lunar"
    # Single wheel: niente house comparison
    assert (
        data.get("house_comparison") in (None, [], {}) or "house_comparison" not in data
    )


def test_lunar_return_single_chart_svg(client: TestClient):
    payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "wheel_type": "single"}
    resp = client.post("/api/v5/chart/lunar-return", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert_api_svg_valid(body["chart"])
    assert body["return_type"] == "Lunar"
    assert body["wheel_type"] == "single"
    assert body["chart_data"]["chart_type"] == "SingleReturnChart"
