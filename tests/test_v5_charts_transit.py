"""
Test espliciti per gli endpoint transit: chart-data e charts.

Punti chiave verificati:
- Tipo grafico "Transit".
- Presenza di due soggetti (natal + transit).
- House comparison presente.
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


def _make_transit_subject() -> Dict[str, object]:
    payload = deepcopy(BASE_SUBJECT)
    payload.update({"year": 2024, "month": 6, "day": 1})
    return payload


def test_transit_chart_data(client: TestClient):
    payload = {
        "first_subject": deepcopy(BASE_SUBJECT),
        "transit_subject": _make_transit_subject(),
    }
    resp = client.post("/api/v5/chart-data/transit", json=payload)
    assert resp.status_code == 200
    data = resp.json()["chart_data"]

    assert data["chart_type"] == "Transit"
    assert "first_subject" in data and "second_subject" in data
    assert data.get("house_comparison") not in (None, [], {})


def test_transit_chart_svg(client: TestClient):
    payload = {
        "first_subject": deepcopy(BASE_SUBJECT),
        "transit_subject": _make_transit_subject(),
    }
    resp = client.post("/api/v5/chart/transit", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert_api_svg_valid(body["chart"])
    assert body["chart_data"]["chart_type"] == "Transit"
