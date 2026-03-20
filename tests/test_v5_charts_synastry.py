"""
Test espliciti per gli endpoint synastry: chart-data e charts.

Controlli focalizzati sui campi tipici della sinastria:
- presence di house_comparison e relationship_score.
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

ROME_SUBJECT: Dict[str, object] = {
    "name": "FastAPI Unit Test",
    "year": 1946,
    "month": 6,
    "day": 16,
    "hour": 10,
    "minute": 10,
    "longitude": 12.4963655,
    "latitude": 41.9027835,
    "city": "Roma",
    "nation": "IT",
    "timezone": "Europe/Rome",
}


def test_synastry_chart_data(client: TestClient):
    payload = {
        "first_subject": deepcopy(BASE_SUBJECT),
        "second_subject": deepcopy(ROME_SUBJECT),
    }
    resp = client.post("/api/v5/chart-data/synastry", json=payload)
    assert resp.status_code == 200
    data = resp.json()["chart_data"]

    assert data["chart_type"] == "Synastry"
    assert "first_subject" in data and "second_subject" in data
    assert data.get("house_comparison") not in (None, [], {})
    # relationship_score ricco di contenuti
    score = data.get("relationship_score")
    assert isinstance(score, dict)
    assert score.get("score_value") is not None


def test_synastry_chart_svg(client: TestClient):
    payload = {
        "first_subject": deepcopy(BASE_SUBJECT),
        "second_subject": deepcopy(ROME_SUBJECT),
    }
    resp = client.post("/api/v5/chart/synastry", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert_api_svg_valid(body["chart"])
    assert body["chart_data"]["chart_type"] == "Synastry"
