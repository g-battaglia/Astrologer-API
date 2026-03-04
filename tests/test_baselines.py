"""
Baseline snapshot tests — confronto 1:1 degli output API.

Ogni scenario chiama un endpoint con input fisso e confronta l'intero output
JSON con un file salvato in tests/baselines/<id>.json.

Uso:
    pytest tests/test_baselines.py -v              # Verifica contro i baseline esistenti
    pytest tests/test_baselines.py --update-baselines -v   # Rigenera tutti i baseline

Se un baseline manca e --update-baselines non è attivo, il test fallisce con
un messaggio che suggerisce la rigenerazione.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Soggetti riutilizzabili (stessi dati usati nei test esistenti)
# ============================================================================

LONDON_SUBJECT: Dict[str, object] = {
    "name": "Baseline Test London",
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
    "name": "Baseline Test Roma",
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

ROME_1990_SUBJECT: Dict[str, object] = {
    "name": "Baseline Test Roma 1990",
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

PARIS_SUBJECT: Dict[str, object] = {
    "name": "Baseline Test Paris",
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

TRANSIT_SUBJECT: Dict[str, object] = {
    "name": "Transit 2024",
    "year": 2024,
    "month": 6,
    "day": 1,
    "hour": 12,
    "minute": 12,
    "longitude": 0,
    "latitude": 51.4825766,
    "city": "London",
    "nation": "GB",
    "timezone": "Europe/London",
}

MOON_PHASE_REQUEST: Dict[str, object] = {
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


# ============================================================================
# Definizione di tutti gli scenari
# ============================================================================

SCENARIOS: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Data endpoints: /api/v5/subject
    # ------------------------------------------------------------------
    {
        "id": "subject_rome",
        "url": "/api/v5/subject",
        "json": {"subject": ROME_SUBJECT},
    },
    {
        "id": "subject_london",
        "url": "/api/v5/subject",
        "json": {"subject": LONDON_SUBJECT},
    },
    {
        "id": "subject_sidereal_lahiri",
        "url": "/api/v5/subject",
        "json": {
            "subject": {
                **ROME_1990_SUBJECT,
                "zodiac_type": "Sidereal",
                "sidereal_mode": "LAHIRI",
            }
        },
    },
    {
        "id": "subject_whole_sign",
        "url": "/api/v5/subject",
        "json": {
            "subject": {
                **ROME_1990_SUBJECT,
                "houses_system_identifier": "W",
            }
        },
    },
    # ------------------------------------------------------------------
    # Data endpoints: /api/v5/now/*
    # ------------------------------------------------------------------
    {
        "id": "now_subject",
        "url": "/api/v5/now/subject",
        "json": {},
    },
    # ------------------------------------------------------------------
    # Data endpoints: /api/v5/chart-data/*
    # ------------------------------------------------------------------
    {
        "id": "chartdata_natal",
        "url": "/api/v5/chart-data/birth-chart",
        "json": {"subject": LONDON_SUBJECT},
    },
    {
        "id": "chartdata_synastry",
        "url": "/api/v5/chart-data/synastry",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "second_subject": ROME_SUBJECT,
        },
    },
    {
        "id": "chartdata_composite",
        "url": "/api/v5/chart-data/composite",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "second_subject": ROME_SUBJECT,
        },
    },
    {
        "id": "chartdata_transit",
        "url": "/api/v5/chart-data/transit",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "transit_subject": TRANSIT_SUBJECT,
        },
    },
    {
        "id": "chartdata_solar_return_dual",
        "url": "/api/v5/chart-data/solar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "dual",
        },
    },
    {
        "id": "chartdata_solar_return_single",
        "url": "/api/v5/chart-data/solar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "single",
        },
    },
    {
        "id": "chartdata_lunar_return_dual",
        "url": "/api/v5/chart-data/lunar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "dual",
        },
    },
    {
        "id": "chartdata_lunar_return_single",
        "url": "/api/v5/chart-data/lunar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "single",
        },
    },
    {
        "id": "chartdata_natal_custom_points",
        "url": "/api/v5/chart-data/birth-chart",
        "json": {
            "subject": ROME_1990_SUBJECT,
            "active_points": ["Sun", "Moon", "Ascendant", "Spica", "Chiron"],
        },
    },
    {
        "id": "chartdata_natal_pure_count",
        "url": "/api/v5/chart-data/birth-chart",
        "json": {
            "subject": ROME_1990_SUBJECT,
            "distribution_method": "pure_count",
        },
    },
    # ------------------------------------------------------------------
    # Data endpoints: /api/v5/compatibility-score
    # ------------------------------------------------------------------
    {
        "id": "compatibility_score",
        "url": "/api/v5/compatibility-score",
        "json": {
            "first_subject": ROME_SUBJECT,
            "second_subject": ROME_SUBJECT,
        },
    },
    # ------------------------------------------------------------------
    # Chart/SVG endpoints: /api/v5/chart/*
    # ------------------------------------------------------------------
    {
        "id": "chart_natal",
        "url": "/api/v5/chart/birth-chart",
        "json": {"subject": LONDON_SUBJECT},
    },
    {
        "id": "chart_synastry",
        "url": "/api/v5/chart/synastry",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "second_subject": ROME_SUBJECT,
        },
    },
    {
        "id": "chart_composite",
        "url": "/api/v5/chart/composite",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "second_subject": ROME_SUBJECT,
        },
    },
    {
        "id": "chart_transit",
        "url": "/api/v5/chart/transit",
        "json": {
            "first_subject": LONDON_SUBJECT,
            "transit_subject": TRANSIT_SUBJECT,
        },
    },
    {
        "id": "chart_solar_return",
        "url": "/api/v5/chart/solar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "dual",
        },
    },
    {
        "id": "chart_lunar_return",
        "url": "/api/v5/chart/lunar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "single",
        },
    },
    {
        "id": "now_chart",
        "url": "/api/v5/now/chart",
        "json": {},
    },
    # ------------------------------------------------------------------
    # Context endpoints: /api/v5/context/*
    # ------------------------------------------------------------------
    {
        "id": "context_subject",
        "url": "/api/v5/context/subject",
        "json": {"subject": ROME_1990_SUBJECT},
    },
    {
        "id": "context_natal",
        "url": "/api/v5/context/birth-chart",
        "json": {"subject": ROME_1990_SUBJECT},
    },
    {
        "id": "context_synastry",
        "url": "/api/v5/context/synastry",
        "json": {
            "first_subject": ROME_1990_SUBJECT,
            "second_subject": PARIS_SUBJECT,
        },
    },
    {
        "id": "context_composite",
        "url": "/api/v5/context/composite",
        "json": {
            "first_subject": ROME_1990_SUBJECT,
            "second_subject": PARIS_SUBJECT,
        },
    },
    {
        "id": "context_transit",
        "url": "/api/v5/context/transit",
        "json": {
            "first_subject": ROME_1990_SUBJECT,
            "transit_subject": {
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
            },
        },
    },
    {
        "id": "context_solar_return",
        "url": "/api/v5/context/solar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "wheel_type": "dual",
        },
    },
    {
        "id": "context_lunar_return",
        "url": "/api/v5/context/lunar-return",
        "json": {
            "subject": LONDON_SUBJECT,
            "year": 2024,
            "month": 6,
            "wheel_type": "single",
        },
    },
    {
        "id": "now_context",
        "url": "/api/v5/now/context",
        "json": {"name": "Now Context Baseline"},
    },
    # ------------------------------------------------------------------
    # Moon phase endpoints: /api/v5/moon-phase/*
    # ------------------------------------------------------------------
    {
        "id": "moon_phase",
        "url": "/api/v5/moon-phase",
        "json": MOON_PHASE_REQUEST,
    },
    {
        "id": "moon_phase_now_utc",
        "url": "/api/v5/moon-phase/now-utc",
        "json": {},
    },
    {
        "id": "moon_phase_context",
        "url": "/api/v5/moon-phase/context",
        "json": MOON_PHASE_REQUEST,
    },
    {
        "id": "moon_phase_now_utc_context",
        "url": "/api/v5/moon-phase/now-utc/context",
        "json": {},
    },
]


# ============================================================================
# Helpers
# ============================================================================


def _pretty_json(obj: Any) -> str:
    """Serializza in JSON leggibile con chiavi ordinate per diff stabili."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _diff_summary(expected: Any, actual: Any, path: str = "$") -> List[str]:
    """Produce un sommario leggibile delle differenze tra due strutture JSON.

    Ritorna al massimo 20 righe per non sommergere l'output del terminale.
    """
    diffs: List[str] = []
    _MAX = 20

    def _walk(exp: Any, act: Any, p: str) -> None:
        if len(diffs) >= _MAX:
            return

        if type(exp) is not type(act):
            diffs.append(f"  {p}: tipo {type(exp).__name__} -> {type(act).__name__}")
            return

        if isinstance(exp, dict):
            all_keys = set(exp) | set(act)
            for k in sorted(all_keys):
                if k not in act:
                    diffs.append(f"  {p}.{k}: RIMOSSO")
                elif k not in exp:
                    diffs.append(f"  {p}.{k}: AGGIUNTO")
                else:
                    _walk(exp[k], act[k], f"{p}.{k}")
                if len(diffs) >= _MAX:
                    return
        elif isinstance(exp, list):
            if len(exp) != len(act):
                diffs.append(f"  {p}: len {len(exp)} -> {len(act)}")
            for i in range(min(len(exp), len(act))):
                _walk(exp[i], act[i], f"{p}[{i}]")
                if len(diffs) >= _MAX:
                    return
        elif exp != act:
            exp_s = (
                repr(exp)
                if not isinstance(exp, str) or len(exp) < 80
                else repr(exp[:60]) + "..."
            )
            act_s = (
                repr(act)
                if not isinstance(act, str) or len(act) < 80
                else repr(act[:60]) + "..."
            )
            diffs.append(f"  {p}: {exp_s} -> {act_s}")

    _walk(expected, actual, path)
    if len(diffs) >= _MAX:
        diffs.append(f"  ... (troncato, troppe differenze)")
    return diffs


# ============================================================================
# Test parametrizzato
# ============================================================================


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_baseline(
    client: TestClient,
    scenario: Dict[str, Any],
    baselines_dir: Path,
    update_baselines: bool,
) -> None:
    """Confronta l'output di un endpoint con il baseline salvato su disco.

    Con --update-baselines scrive/aggiorna il file e salta il test.
    Senza il flag, confronta 1:1 e fallisce con diff leggibile se diverso.
    """
    resp = client.post(scenario["url"], json=deepcopy(scenario["json"]))
    assert resp.status_code == 200, (
        f"[{scenario['id']}] Expected 200, got {resp.status_code}: {resp.text[:500]}"
    )

    actual = resp.json()
    baseline_path = baselines_dir / f"{scenario['id']}.json"

    # -- Modalità aggiornamento: scrivi e salta --
    if update_baselines:
        baseline_path.write_text(_pretty_json(actual), encoding="utf-8")
        pytest.skip(f"Baseline scritto: {baseline_path.name}")
        return

    # -- Modalità verifica: confronta con il file esistente --
    assert baseline_path.exists(), (
        f"Baseline mancante: {baseline_path.name}\n"
        f"Esegui: pytest tests/test_baselines.py --update-baselines -v"
    )

    expected = json.loads(baseline_path.read_text(encoding="utf-8"))

    if actual != expected:
        diff_lines = _diff_summary(expected, actual)
        diff_text = "\n".join(diff_lines)
        pytest.fail(
            f"Output diverge dal baseline '{scenario['id']}'.\n"
            f"\nDifferenze:\n{diff_text}\n"
            f"\nSe il cambiamento è intenzionale, rigenera con:\n"
            f"  pytest tests/test_baselines.py --update-baselines -v\n"
            f"  # oppure: poe update-baselines"
        )
