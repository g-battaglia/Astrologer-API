"""
Test degli scenari di errore più significativi, scritti in modo esplicito.

Copertura minima ma chiara:
- Errore GeoNames: quando si richiede la risoluzione online e la chiamata fallisce, l'API risponde 400 con messaggio dedicato.
- Errore generico interno: simulato patchando la factory per generare un 500 standardizzato.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

import pytest
from fastapi.testclient import TestClient


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


def test_error_geonames_path_on_subject(client: TestClient):
    """Geonames richiesto senza coordinate/timezone: l'API risponde 400 con messaggio contestuale."""
    payload = deepcopy(BASE_SUBJECT)
    # Rimuovo coordinate/timezone per forzare risoluzione online e simulare errore
    payload.pop("longitude")
    payload.pop("latitude")
    payload.pop("timezone")
    payload["geonames_username"] = "fake-user"

    resp = client.post("/api/v5/subject", json={"subject": payload})
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "ERROR"
    assert body["error_type"] == "GeoNamesLookupError"
    assert "London" in body["message"]
    assert body["details"]["city"] == "London"
    assert body["details"]["nation"] == "GB"
    assert body["details"]["error_category"] == "city_not_found"


def test_error_internal_500_on_natal_chart(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Simuliamo un errore interno patchando la factory dei dati del grafico natal."""

    def boom(*args, **kwargs):  # pragma: no cover - funzione di patch
        raise RuntimeError("Boom")

    monkeypatch.setattr("app.routers.charts.create_natal_chart_data", boom)

    resp = client.post("/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)})
    assert resp.status_code == 500
    assert resp.json() == {
        "status": "ERROR",
        "message": "Boom",
        "error_type": "RuntimeError",
    }
