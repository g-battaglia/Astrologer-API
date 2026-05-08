"""Verifies that errors are correctly exposed in API responses."""

from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from kerykeion.schemas import KerykeionException


SUBJECT_TEMPLATE = {
    "name": "Error Handling Test",
    "year": 1985,
    "month": 7,
    "day": 3,
    "hour": 9,
    "minute": 15,
    "longitude": 12.4963655,
    "latitude": 41.9027835,
    "city": "Rome",
    "nation": "IT",
    "timezone": "Europe/Rome",
}


def _build_subject_payload() -> dict[str, object]:
    return deepcopy(SUBJECT_TEMPLATE)


def _build_lunar_return_payload() -> dict[str, object]:
    return {
        "subject": _build_subject_payload(),
        "year": 2024,
        "wheel_type": "single",
    }


def _build_natal_chart_payload() -> dict[str, object]:
    return {"subject": _build_subject_payload()}


def test_lunar_return_domain_error_exposes_message(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    error_message = "Moon position is required for Lunar return but is not available in the subject."

    def raise_domain_error(*_: object, **__: object) -> None:
        raise KerykeionException(error_message)

    monkeypatch.setattr(
        "app.routers.charts.calculate_return_chart_data",
        raise_domain_error,
    )

    response = client.post("/api/v5/chart/lunar-return", json=_build_lunar_return_payload())

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["message"] == error_message
    assert body["error_type"] == "KerykeionException"


def test_invalid_date_returns_422(client: TestClient) -> None:
    payload = _build_natal_chart_payload()
    payload["subject"]["year"] = 2025
    payload["subject"]["month"] = 2
    payload["subject"]["day"] = 29
    resp = client.post("/api/v5/chart/birth-chart", json=payload)
    assert resp.status_code == 422


def test_invalid_date_moon_phase_returns_422(client: TestClient) -> None:
    payload = {
        "year": 2025,
        "month": 2,
        "day": 29,
        "hour": 12,
        "minute": 0,
        "latitude": 51.5074,
        "longitude": -0.1276,
        "timezone": "Europe/London",
    }
    resp = client.post("/api/v5/moon-phase", json=payload)
    assert resp.status_code == 422


def test_natal_chart_unexpected_error_exposes_message(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    error_message = "Unexpected failure"

    def raise_generic_error(*_: object, **__: object) -> None:
        raise RuntimeError(error_message)

    monkeypatch.setattr(
        "app.routers.data.create_natal_chart_data",
        raise_generic_error,
    )

    response = client.post("/api/v5/chart-data/birth-chart", json=_build_natal_chart_payload())

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["message"] == error_message
    assert body["error_type"] == "RuntimeError"


# ---------------------------------------------------------------------------
# GeoNames error classification tests
# ---------------------------------------------------------------------------

def _build_geonames_chart_payload() -> dict[str, object]:
    """Build a payload that uses geonames_username instead of coordinates."""
    payload = deepcopy(SUBJECT_TEMPLATE)
    del payload["longitude"]
    del payload["latitude"]
    del payload["timezone"]
    payload["geonames_username"] = "test-user"
    return {"subject": payload}


def test_geonames_city_not_found_includes_context(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def raise_missing(*_: object, **__: object) -> None:
        raise KerykeionException(
            "Missing data from geonames: countryCode, timezonestr, lat, lng. "
            "Check your connection or try a different location."
        )

    monkeypatch.setattr("app.routers.charts.create_natal_chart_data", raise_missing)

    response = client.post("/api/v5/chart/birth-chart", json=_build_geonames_chart_payload())
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["error_type"] == "GeoNamesLookupError"
    assert body["details"]["city"] == "Rome"
    assert body["details"]["nation"] == "IT"
    assert body["details"]["error_category"] == "city_not_found"
    assert "Rome" in body["message"]
    assert "hint" in body


def test_geonames_timeout_returns_504(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def raise_timeout(*_: object, **__: object) -> None:
        raise KerykeionException("ConnectTimeout: GeoNames API timed out.")

    monkeypatch.setattr("app.routers.charts.create_natal_chart_data", raise_timeout)

    response = client.post("/api/v5/chart/birth-chart", json=_build_geonames_chart_payload())
    assert response.status_code == 504
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["details"]["error_category"] == "timeout"
    assert "Rome" in body["message"]


def test_geonames_connection_error_returns_502(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def raise_conn_error(*_: object, **__: object) -> None:
        raise KerykeionException("ConnectionError: could not reach api.geonames.org")

    monkeypatch.setattr("app.routers.charts.create_natal_chart_data", raise_conn_error)

    response = client.post("/api/v5/chart/birth-chart", json=_build_geonames_chart_payload())
    assert response.status_code == 502
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["details"]["error_category"] == "connection_error"


def test_non_geonames_error_unchanged(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    """Non-GeoNames errors keep the original behavior (400 for KerykeionException, 500 for others)."""
    def raise_domain(*_: object, **__: object) -> None:
        raise KerykeionException("Some unrelated domain error")

    monkeypatch.setattr("app.routers.charts.create_natal_chart_data", raise_domain)

    response = client.post("/api/v5/chart/birth-chart", json=_build_geonames_chart_payload())
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "ERROR"
    assert body["message"] == "Some unrelated domain error"
    assert body["error_type"] == "KerykeionException"
    assert "details" not in body
