"""
SVG well-formedness and CSS variables anti-regression tests.

These tests exist to prevent regressions like:
- Minification bug (kerykeion b5e7013): ``<svgxmlns=...>`` instead of ``<svg xmlns=...>``
- CSS variable stripping (API e288003): ``remove_css_variables=True`` broke consumer restyling

The key assertion — ``ElementTree.fromstring()`` — catches any malformed XML
regardless of the specific failure mode.  These tests cover all chart endpoints
that return SVG: natal, synastry, transit, composite, solar return, lunar return,
now/chart, and split-chart variants.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from tests.conftest import assert_api_svg_valid


# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

BASE_SUBJECT: Dict[str, object] = {
    "name": "SVG Validation Test",
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

SECOND_SUBJECT: Dict[str, object] = {
    "name": "SVG Validation Test B",
    "year": 1985,
    "month": 6,
    "day": 20,
    "hour": 14,
    "minute": 30,
    "longitude": 12.4964,
    "latitude": 41.9028,
    "city": "Rome",
    "nation": "IT",
    "timezone": "Europe/Rome",
}

TRANSIT_SUBJECT: Dict[str, object] = {
    "year": 2024,
    "month": 6,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "longitude": 0,
    "latitude": 51.4825766,
    "city": "London",
    "nation": "GB",
    "timezone": "Europe/London",
}


# =============================================================================
# SVG Well-formedness: every chart endpoint must return valid, parseable SVG
# =============================================================================


class TestSvgWellformedness:
    """Validate that every chart endpoint returns well-formed XML SVG."""

    def test_natal_chart_svg_is_valid(self, client: TestClient):
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_synastry_chart_svg_is_valid(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/synastry", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_transit_chart_svg_is_valid(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "transit_subject": deepcopy(TRANSIT_SUBJECT),
        }
        resp = client.post("/api/v5/chart/transit", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_composite_chart_svg_is_valid(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/composite", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_solar_return_chart_svg_is_valid(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025}
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_lunar_return_chart_svg_is_valid(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025, "month": 1}
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_now_chart_svg_is_valid(self, client: TestClient):
        resp = client.post("/api/v5/now/chart", json={})
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])


# =============================================================================
# Split chart: wheel + grid must both be valid SVG
# =============================================================================


class TestSplitChartSvgWellformedness:
    """Validate split_chart=true returns two valid SVG strings."""

    def test_natal_split_chart_both_valid(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "split_chart": True}
        resp = client.post("/api/v5/chart/birth-chart", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart_wheel"])
        assert_api_svg_valid(body["chart_grid"])

    def test_transit_split_chart_both_valid(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "transit_subject": deepcopy(TRANSIT_SUBJECT),
            "split_chart": True,
        }
        resp = client.post("/api/v5/chart/transit", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart_wheel"])
        assert_api_svg_valid(body["chart_grid"])

    def test_synastry_split_chart_both_valid(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
            "split_chart": True,
        }
        resp = client.post("/api/v5/chart/synastry", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart_wheel"])
        assert_api_svg_valid(body["chart_grid"])


# =============================================================================
# CSS Variables: SVG must contain CSS custom properties for consumer restyling
# =============================================================================


class TestCssVariablesPreserved:
    """Ensure CSS custom properties are present in all chart SVG output.

    CSS variables (``var(--kerykeion-…)``) are the public styling API for
    consumers who embed the chart SVG in their pages.  Stripping them
    breaks their ability to restyle charts with custom colors.
    """

    def test_natal_has_css_variables(self, client: TestClient):
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Natal SVG must contain CSS custom properties"
        assert "<style" in svg, "Natal SVG must contain <style> block"

    def test_transit_has_css_variables(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "transit_subject": deepcopy(TRANSIT_SUBJECT),
        }
        resp = client.post("/api/v5/chart/transit", json=payload)
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Transit SVG must contain CSS custom properties"
        assert "<style" in svg, "Transit SVG must contain <style> block"

    def test_synastry_has_css_variables(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/synastry", json=payload)
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Synastry SVG must contain CSS custom properties"
        assert "<style" in svg, "Synastry SVG must contain <style> block"

    def test_composite_has_css_variables(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/composite", json=payload)
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Composite SVG must contain CSS custom properties"
        assert "<style" in svg, "Composite SVG must contain <style> block"

    def test_solar_return_has_css_variables(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025}
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Solar return SVG must contain CSS custom properties"
        assert "<style" in svg, "Solar return SVG must contain <style> block"

    def test_lunar_return_has_css_variables(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025, "month": 1}
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        svg = resp.json()["chart"]
        assert "var(--" in svg, "Lunar return SVG must contain CSS custom properties"
        assert "<style" in svg, "Lunar return SVG must contain <style> block"

    def test_split_chart_wheel_has_css_variables(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "split_chart": True}
        resp = client.post("/api/v5/chart/birth-chart", json=payload)
        body = resp.json()
        assert "var(--" in body["chart_wheel"], (
            "Split chart wheel must contain CSS custom properties"
        )
        assert "var(--" in body["chart_grid"], (
            "Split chart grid must contain CSS custom properties"
        )


# =============================================================================
# Strengthen existing smoke checks: replace weak assert with full validation
# =============================================================================


class TestExistingEndpointsUpgradedValidation:
    """Replace weak '<svg' in string checks with full XML parsing validation.

    These tests mirror the existing endpoint tests but use
    assert_api_svg_valid() instead of ``assert '<svg' in body['chart']``.
    """

    def test_natal_upgraded(self, client: TestClient):
        resp = client.post(
            "/api/v5/chart/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_synastry_upgraded(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/synastry", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_transit_upgraded(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "transit_subject": deepcopy(TRANSIT_SUBJECT),
        }
        resp = client.post("/api/v5/chart/transit", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_composite_upgraded(self, client: TestClient):
        payload = {
            "first_subject": deepcopy(BASE_SUBJECT),
            "second_subject": deepcopy(SECOND_SUBJECT),
        }
        resp = client.post("/api/v5/chart/composite", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_solar_return_upgraded(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025}
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_lunar_return_upgraded(self, client: TestClient):
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2025, "month": 1}
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])

    def test_now_chart_upgraded(self, client: TestClient):
        resp = client.post("/api/v5/now/chart", json={})
        assert resp.status_code == 200
        assert_api_svg_valid(resp.json()["chart"])
