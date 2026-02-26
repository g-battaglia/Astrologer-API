"""
Configurazione test condivisa e minimale.

Obiettivi:
- Esporre un `client` FastAPI riutilizzabile.
- Congelare il tempo usato dagli endpoint `now/*` per risultati deterministici.

Nota: manteniamo tutto molto esplicito e commentato. Nessuna astrazione non necessaria.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from sys import path

import os
import pytest
from fastapi.testclient import TestClient

# Imposta l'ambiente di test prima di importare l'app
os.environ["ENV_TYPE"] = "test"

# Rende importabile la root del repository quando pytest cambia CWD
path.append(str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402


# Silenzia un warning noto su utcnow nelle dipendenze
pytestmark = pytest.mark.filterwarnings("ignore:datetime.datetime.utcnow")

# Timestamp fisso per gli endpoint /api/v5/now/*
FREEZE_TIME = datetime(2024, 6, 1, 12, 30, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Client FastAPI riutilizzabile per i test di integrazione sugli endpoint."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def freeze_time(monkeypatch: pytest.MonkeyPatch):
    """Congela la sorgente del tempo usata dagli endpoint `now/*`.

    Patchiamo la funzione `get_time_from_google` per restituire sempre FREEZE_TIME.
    Questo rende riproducibili i test che controllano timestamp e output correlati.
    """
    monkeypatch.setattr("app.routers.charts.get_time_from_google", lambda: FREEZE_TIME)
    monkeypatch.setattr("app.routers.context.get_time_from_google", lambda: FREEZE_TIME)
    monkeypatch.setattr("app.routers.data.get_time_from_google", lambda: FREEZE_TIME)
    monkeypatch.setattr(
        "app.routers.moon_phase.get_time_from_google", lambda: FREEZE_TIME
    )
    yield
