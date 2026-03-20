"""
Test per le opzioni di rendering dei chart SVG.

Obiettivi:
- Verificare tutti i temi disponibili (classic, dark, light, etc.)
- Verificare tutte le lingue supportate
- Verificare transparent_background
- Verificare custom_title
- Verificare le opzioni show_* (house comparison, degree indicators, aspect icons)
- Verificare split_chart
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from tests.conftest import assert_api_svg_valid


# ============================================================================
# Soggetto di test standard
# ============================================================================

BASE_SUBJECT: Dict[str, object] = {
    "name": "Rendering Test",
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 12,
    "minute": 0,
    "longitude": 12.4964,
    "latitude": 41.9028,
    "city": "Rome",
    "nation": "IT",
    "timezone": "Europe/Rome",
}

SECOND_SUBJECT: Dict[str, object] = {
    "name": "Second Subject",
    "year": 1985,
    "month": 3,
    "day": 20,
    "hour": 10,
    "minute": 30,
    "longitude": 2.3522,
    "latitude": 48.8566,
    "city": "Paris",
    "nation": "FR",
    "timezone": "Europe/Paris",
}


# ============================================================================
# Test per Temi
# ============================================================================


class TestChartThemes:
    """Test per i diversi temi di chart disponibili."""

    def test_theme_classic_default(self, client: TestClient):
        """Verifica che classic sia il tema di default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart" in body
        assert_api_svg_valid(body["chart"])

    def test_theme_classic_explicit(self, client: TestClient):
        """Verifica il tema classic esplicito."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "classic",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_theme_dark(self, client: TestClient):
        """Verifica il tema dark."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "dark",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_theme_light(self, client: TestClient):
        """Verifica il tema light."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "light",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_theme_dark_high_contrast(self, client: TestClient):
        """Verifica il tema dark-high-contrast."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "dark-high-contrast",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_theme_classic_bw(self, client: TestClient):
        """Verifica il tema black-and-white (bianco e nero)."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "black-and-white",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_invalid_theme_returns_422(self, client: TestClient):
        """Verifica che un tema invalido restituisca 422."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "invalid-theme",
            },
        )
        assert resp.status_code == 422


# ============================================================================
# Test per Lingue
# ============================================================================


class TestChartLanguages:
    """Test per le diverse lingue supportate."""

    def test_language_english_default(self, client: TestClient):
        """Verifica che EN sia la lingua di default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        # L'SVG dovrebbe contenere testo in inglese
        chart = resp.json()["chart"]
        assert "<svg" in chart

    def test_language_english_explicit(self, client: TestClient):
        """Verifica lingua inglese esplicita."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "EN",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_italian(self, client: TestClient):
        """Verifica lingua italiana."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "IT",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_spanish(self, client: TestClient):
        """Verifica lingua spagnola."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "ES",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_french(self, client: TestClient):
        """Verifica lingua francese."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "FR",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_german(self, client: TestClient):
        """Verifica lingua tedesca."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "DE",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_portuguese(self, client: TestClient):
        """Verifica lingua portoghese."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "PT",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_russian(self, client: TestClient):
        """Verifica lingua russa."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "RU",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_turkish(self, client: TestClient):
        """Verifica lingua turca."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "TR",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_chinese(self, client: TestClient):
        """Verifica lingua cinese."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "CN",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_language_hindi(self, client: TestClient):
        """Verifica lingua hindi."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "language": "HI",
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]


# ============================================================================
# Test per Transparent Background
# ============================================================================


class TestTransparentBackground:
    """Test per l'opzione transparent_background."""

    def test_transparent_background_false_default(self, client: TestClient):
        """Verifica che transparent_background=false sia il default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        # Il chart dovrebbe avere un background
        chart = resp.json()["chart"]
        assert "<svg" in chart

    def test_transparent_background_true(self, client: TestClient):
        """Verifica transparent_background=true."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "transparent_background": True,
            },
        )
        assert resp.status_code == 200
        chart = resp.json()["chart"]
        assert "<svg" in chart

    def test_transparent_background_false_explicit(self, client: TestClient):
        """Verifica transparent_background=false esplicito."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "transparent_background": False,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]


# ============================================================================
# Test per Custom Title
# ============================================================================


class TestCustomTitle:
    """Test per l'opzione custom_title."""

    def test_no_custom_title_uses_subject_name(self, client: TestClient):
        """Verifica che senza custom_title venga usato il nome del soggetto."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200

        chart = resp.json()["chart"]
        # Il nome del soggetto dovrebbe essere nel chart
        assert "Rendering Test" in chart

    def test_custom_title_applied(self, client: TestClient):
        """Verifica che custom_title venga applicato."""
        custom = "My Custom Chart Title"
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "custom_title": custom,
            },
        )
        assert resp.status_code == 200

        chart = resp.json()["chart"]
        # Il titolo custom dovrebbe essere nel chart
        assert custom in chart

    def test_custom_title_max_length(self, client: TestClient):
        """Verifica che custom_title rispetti il limite di 40 caratteri."""
        # Titolo valido (40 caratteri)
        valid_title = "A" * 40
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "custom_title": valid_title,
            },
        )
        assert resp.status_code == 200

        # Titolo troppo lungo (41 caratteri)
        invalid_title = "A" * 41
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "custom_title": invalid_title,
            },
        )
        assert resp.status_code == 422

    def test_custom_title_empty_string_ignored(self, client: TestClient):
        """Verifica che una stringa vuota per custom_title venga ignorata."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "custom_title": "",
            },
        )
        assert resp.status_code == 200
        # Dovrebbe usare il nome del soggetto
        assert "Rendering Test" in resp.json()["chart"]


# ============================================================================
# Test per Split Chart
# ============================================================================


class TestSplitChart:
    """Test per l'opzione split_chart."""

    def test_split_chart_false_default(self, client: TestClient):
        """Verifica che split_chart=false sia il default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart" in body
        assert "chart_wheel" not in body
        assert "chart_grid" not in body

    def test_split_chart_true(self, client: TestClient):
        """Verifica split_chart=true."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "split_chart": True,
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart" not in body
        assert "chart_wheel" in body
        assert "chart_grid" in body
        assert_api_svg_valid(body["chart_wheel"])
        assert_api_svg_valid(body["chart_grid"])

    def test_split_chart_false_explicit(self, client: TestClient):
        """Verifica split_chart=false esplicito."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "split_chart": False,
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart" in body
        assert "chart_wheel" not in body

    def test_split_chart_works_for_synastry(self, client: TestClient):
        """Verifica che split_chart funzioni per synastry."""
        resp = client.post(
            "/api/v5/chart/synastry",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "second_subject": deepcopy(SECOND_SUBJECT),
                "split_chart": True,
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart_wheel" in body
        assert "chart_grid" in body


# ============================================================================
# Test per Show Options
# ============================================================================


class TestShowOptions:
    """Test per le opzioni show_*."""

    def test_show_house_position_comparison_true_default(self, client: TestClient):
        """Verifica che show_house_position_comparison=true sia il default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_house_position_comparison_false(self, client: TestClient):
        """Verifica show_house_position_comparison=false."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "show_house_position_comparison": False,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_cusp_position_comparison_true_default(self, client: TestClient):
        """Verifica che show_cusp_position_comparison=true sia il default."""
        resp = client.post(
            "/api/v5/chart/synastry",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "second_subject": deepcopy(SECOND_SUBJECT),
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_cusp_position_comparison_false(self, client: TestClient):
        """Verifica show_cusp_position_comparison=false."""
        resp = client.post(
            "/api/v5/chart/synastry",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "second_subject": deepcopy(SECOND_SUBJECT),
                "show_cusp_position_comparison": False,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_degree_indicators_true_default(self, client: TestClient):
        """Verifica che show_degree_indicators=true sia il default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_degree_indicators_false(self, client: TestClient):
        """Verifica show_degree_indicators=false."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "show_degree_indicators": False,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_aspect_icons_true_default(self, client: TestClient):
        """Verifica che show_aspect_icons=true sia il default."""
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_show_aspect_icons_false(self, client: TestClient):
        """Verifica show_aspect_icons=false."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "show_aspect_icons": False,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]


# ============================================================================
# Test per combinazioni di opzioni di rendering
# ============================================================================


class TestRenderingCombinations:
    """Test per combinazioni di opzioni di rendering."""

    def test_dark_theme_with_transparent_background(self, client: TestClient):
        """Verifica combinazione dark + transparent."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "dark",
                "transparent_background": True,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_all_options_combined(self, client: TestClient):
        """Verifica tutte le opzioni combinate."""
        resp = client.post(
            "/api/v5/chart/birth-chart",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "theme": "light",
                "language": "IT",
                "split_chart": True,
                "transparent_background": True,
                "show_house_position_comparison": False,
                "show_degree_indicators": False,
                "show_aspect_icons": False,
                "custom_title": "Test Completo",
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart_wheel" in body
        assert "chart_grid" in body
        assert "Test Completo" in body["chart_wheel"]

    def test_rendering_options_in_synastry(self, client: TestClient):
        """Verifica opzioni di rendering in synastry."""
        resp = client.post(
            "/api/v5/chart/synastry",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "second_subject": deepcopy(SECOND_SUBJECT),
                "theme": "dark",
                "language": "FR",
                "custom_title": "Synastry Test",
            },
        )
        assert resp.status_code == 200

        chart = resp.json()["chart"]
        assert "<svg" in chart
        assert "Synastry Test" in chart

    def test_rendering_options_in_composite(self, client: TestClient):
        """Verifica opzioni di rendering in composite."""
        resp = client.post(
            "/api/v5/chart/composite",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "second_subject": deepcopy(SECOND_SUBJECT),
                "theme": "black-and-white",
                "split_chart": True,
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart_wheel" in body
        assert "chart_grid" in body

    def test_rendering_options_in_transit(self, client: TestClient):
        """Verifica opzioni di rendering in transit."""
        transit = deepcopy(BASE_SUBJECT)
        transit["name"] = "Transit"
        transit["year"] = 2025

        resp = client.post(
            "/api/v5/chart/transit",
            json={
                "first_subject": deepcopy(BASE_SUBJECT),
                "transit_subject": transit,
                "theme": "light",
                "transparent_background": True,
            },
        )
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_rendering_options_in_now_chart(self, client: TestClient):
        """Verifica opzioni di rendering in now/chart."""
        resp = client.post(
            "/api/v5/now/chart",
            json={
                "theme": "dark",
                "language": "ES",
                "split_chart": True,
                "custom_title": "Now Chart",
            },
        )
        assert resp.status_code == 200

        body = resp.json()
        assert "chart_wheel" in body
        assert "Now Chart" in body["chart_wheel"]
