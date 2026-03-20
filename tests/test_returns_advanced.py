"""
Advanced tests for Solar and Lunar Return endpoints.

Tests cover:
- Year only vs year+month+day search parameters
- iso_datetime format for returns
- return_location overrides (offline with coordinates, online with geonames)
- Single vs dual wheel types and their data structures
- Context endpoints for returns
- Validation errors
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from tests.conftest import assert_api_svg_valid


BASE_SUBJECT: Dict[str, object] = {
    "name": "Return Test Subject",
    "year": 1985,
    "month": 6,
    "day": 21,
    "hour": 14,
    "minute": 30,
    "longitude": -0.1276,
    "latitude": 51.5074,
    "city": "London",
    "nation": "GB",
    "timezone": "Europe/London",
}


class TestSolarReturnSearchParameters:
    """Test different search parameter combinations for solar return."""

    def test_solar_return_year_only(self, client: TestClient):
        """Solar return with year only searches for next birthday in that year."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        # Should find a return in 2024
        assert "subject" in data or "second_subject" in data

    def test_solar_return_year_and_month(self, client: TestClient):
        """Solar return with year and month starts search from that month."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "month": 1}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None

    def test_solar_return_year_month_day(self, client: TestClient):
        """Solar return with year, month, and day starts search from that date."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "month": 6,
            "day": 15,
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None

    def test_solar_return_iso_datetime(self, client: TestClient):
        """Solar return with iso_datetime uses that as search starting point."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "iso_datetime": "2024-06-01T00:00:00+00:00",
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None


class TestLunarReturnSearchParameters:
    """Test different search parameter combinations for lunar return."""

    def test_lunar_return_year_only(self, client: TestClient):
        """Lunar return with year only."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024}
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None

    def test_lunar_return_year_and_month(self, client: TestClient):
        """Lunar return with year and month."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "month": 3}
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None

    def test_lunar_return_iso_datetime(self, client: TestClient):
        """Lunar return with iso_datetime."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "iso_datetime": "2024-03-15T12:00:00+00:00",
        }
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None


class TestWheelTypes:
    """Test single vs dual wheel types for returns."""

    def test_solar_return_dual_wheel_default(self, client: TestClient):
        """Dual wheel is the default and includes house comparison."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data["chart_type"] == "DualReturnChart"
        # Dual wheel should have second_subject with return data
        assert "second_subject" in data
        assert data["second_subject"]["return_type"] == "Solar"
        # Should have house comparison
        assert data.get("house_comparison") not in (None, [], {})

    def test_solar_return_single_wheel(self, client: TestClient):
        """Single wheel shows only the return chart without natal."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data["chart_type"] == "SingleReturnChart"
        # Single wheel has subject (not second_subject)
        assert "subject" in data
        assert data["subject"]["return_type"] == "Solar"
        # No house comparison in single wheel
        assert (
            data.get("house_comparison") in (None, [], {})
            or "house_comparison" not in data
        )

    def test_lunar_return_dual_wheel(self, client: TestClient):
        """Lunar return with dual wheel."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "dual",
        }
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data["chart_type"] == "DualReturnChart"
        assert data["second_subject"]["return_type"] == "Lunar"

    def test_lunar_return_single_wheel(self, client: TestClient):
        """Lunar return with single wheel."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data["chart_type"] == "SingleReturnChart"
        assert data["subject"]["return_type"] == "Lunar"


class TestReturnLocation:
    """Test return_location override for relocated returns."""

    def test_solar_return_with_return_location_coordinates(self, client: TestClient):
        """Return location can be specified with coordinates (offline mode)."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "return_location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
                "city": "New York",
                "nation": "US",
            },
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        # The return chart should use the new location
        # This is reflected in the return subject's location
        return_subject = data.get("second_subject") or data.get("subject")
        assert return_subject is not None

    def test_lunar_return_with_return_location(self, client: TestClient):
        """Lunar return with relocated location."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "return_location": {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timezone": "Europe/Paris",
                "city": "Paris",
                "nation": "FR",
            },
        }
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert data is not None

    def test_return_location_validation_incomplete_coordinates(
        self, client: TestClient
    ):
        """Return location requires all coordinates or geonames."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "return_location": {
                "latitude": 40.7128,
                # Missing longitude and timezone
            },
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 422


class TestReturnChartEndpoints:
    """Test chart endpoints (with SVG) for returns."""

    def test_solar_return_chart_dual(self, client: TestClient):
        """Solar return chart endpoint returns SVG and metadata."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "dual",
        }
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart"])
        assert body["return_type"] == "Solar"
        assert body["wheel_type"] == "dual"
        assert body["chart_data"]["chart_type"] == "DualReturnChart"

    def test_solar_return_chart_single(self, client: TestClient):
        """Solar return chart with single wheel."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart"])
        assert body["return_type"] == "Solar"
        assert body["wheel_type"] == "single"
        assert body["chart_data"]["chart_type"] == "SingleReturnChart"

    def test_lunar_return_chart_dual(self, client: TestClient):
        """Lunar return chart with dual wheel."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "dual",
        }
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart"])
        assert body["return_type"] == "Lunar"
        assert body["wheel_type"] == "dual"

    def test_lunar_return_chart_single(self, client: TestClient):
        """Lunar return chart with single wheel."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert_api_svg_valid(body["chart"])
        assert body["return_type"] == "Lunar"
        assert body["wheel_type"] == "single"


class TestReturnContextEndpoints:
    """Test context endpoints for returns."""

    def test_solar_return_context(self, client: TestClient):
        """Solar return context endpoint."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024}
        resp = client.post("/api/v5/context/solar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "OK"
        assert "context" in body
        assert isinstance(body["context"], str)
        assert len(body["context"]) > 100  # Should have meaningful content

    def test_lunar_return_context(self, client: TestClient):
        """Lunar return context endpoint."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024}
        resp = client.post("/api/v5/context/lunar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "OK"
        assert "context" in body
        assert isinstance(body["context"], str)


class TestReturnRenderingOptions:
    """Test rendering options for return charts."""

    @pytest.mark.parametrize("theme", ["classic", "dark", "light"])
    def test_solar_return_chart_themes(self, client: TestClient, theme: str):
        """Solar return chart with different themes."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "theme": theme,
        }
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    @pytest.mark.parametrize("language", ["EN", "IT", "FR", "DE"])
    def test_lunar_return_chart_languages(self, client: TestClient, language: str):
        """Lunar return chart with different languages."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "language": language,
        }
        resp = client.post("/api/v5/chart/lunar-return", json=payload)
        assert resp.status_code == 200
        assert "<svg" in resp.json()["chart"]

    def test_solar_return_split_chart(self, client: TestClient):
        """Solar return with split_chart option."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "split_chart": True,
        }
        resp = client.post("/api/v5/chart/solar-return", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # Split chart returns wheel and grid
        assert "chart_wheel" in body or "chart" in body


class TestReturnValidationErrors:
    """Test validation errors for return endpoints."""

    def test_solar_return_missing_search_params(self, client: TestClient):
        """Error when neither year nor iso_datetime provided."""
        payload = {"subject": deepcopy(BASE_SUBJECT)}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 422

    def test_solar_return_month_without_year(self, client: TestClient):
        """Error when month provided without year."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "month": 6}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 422

    def test_solar_return_day_without_month(self, client: TestClient):
        """Error when day provided without month."""
        payload = {"subject": deepcopy(BASE_SUBJECT), "year": 2024, "day": 15}
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        # Day without month is allowed if day is 1 (default)
        # But day != 1 without month should error
        assert resp.status_code == 422

    def test_lunar_return_invalid_wheel_type(self, client: TestClient):
        """Error for invalid wheel_type."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "triple",
        }
        resp = client.post("/api/v5/chart-data/lunar-return", json=payload)
        assert resp.status_code == 422


class TestReturnDataIntegrity:
    """Test data integrity in return charts."""

    def test_solar_return_has_planets(self, client: TestClient):
        """Solar return data includes planetary positions in the subject."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        # In returns, planets are directly on the subject object
        subj = data["subject"]
        assert "sun" in subj
        assert "moon" in subj
        assert "mercury" in subj
        assert subj["sun"]["abs_pos"] is not None

    def test_solar_return_sun_position_matches_natal(self, client: TestClient):
        """In solar return, Sun position should match natal Sun position."""
        # Get natal Sun position
        natal_resp = client.post(
            "/api/v5/chart-data/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        natal_data = natal_resp.json()["chart_data"]
        natal_sun = natal_data["subject"]["sun"]
        natal_sun_pos = natal_sun["abs_pos"]

        # Get solar return
        return_resp = client.post(
            "/api/v5/chart-data/solar-return",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "year": 2024,
                "wheel_type": "single",
            },
        )
        return_data = return_resp.json()["chart_data"]
        return_sun = return_data["subject"]["sun"]
        return_sun_pos = return_sun["abs_pos"]

        # Sun positions should be very close (within 1 degree)
        diff = abs(natal_sun_pos - return_sun_pos)
        # Handle wraparound at 360
        if diff > 180:
            diff = 360 - diff
        assert diff < 1.0, (
            f"Solar return Sun ({return_sun_pos}) should match natal Sun ({natal_sun_pos})"
        )

    def test_lunar_return_moon_position_matches_natal(self, client: TestClient):
        """In lunar return, Moon position should match natal Moon position."""
        # Get natal Moon position
        natal_resp = client.post(
            "/api/v5/chart-data/birth-chart", json={"subject": deepcopy(BASE_SUBJECT)}
        )
        natal_data = natal_resp.json()["chart_data"]
        natal_moon = natal_data["subject"]["moon"]
        natal_moon_pos = natal_moon["abs_pos"]

        # Get lunar return
        return_resp = client.post(
            "/api/v5/chart-data/lunar-return",
            json={
                "subject": deepcopy(BASE_SUBJECT),
                "year": 2024,
                "wheel_type": "single",
            },
        )
        return_data = return_resp.json()["chart_data"]
        return_moon = return_data["subject"]["moon"]
        return_moon_pos = return_moon["abs_pos"]

        # Moon positions should be very close (within 1 degree)
        diff = abs(natal_moon_pos - return_moon_pos)
        if diff > 180:
            diff = 360 - diff
        assert diff < 1.0, (
            f"Lunar return Moon ({return_moon_pos}) should match natal Moon ({natal_moon_pos})"
        )

    def test_return_has_houses(self, client: TestClient):
        """Return chart data includes house cusps in the subject."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        subj = data["subject"]
        # Houses are directly on the subject as first_house, second_house, etc.
        assert "first_house" in subj
        assert "twelfth_house" in subj
        assert subj["first_house"]["abs_pos"] is not None

    def test_return_has_aspects(self, client: TestClient):
        """Return chart data includes aspects."""
        payload = {
            "subject": deepcopy(BASE_SUBJECT),
            "year": 2024,
            "wheel_type": "single",
        }
        resp = client.post("/api/v5/chart-data/solar-return", json=payload)
        assert resp.status_code == 200
        data = resp.json()["chart_data"]
        assert "aspects" in data
        # Should have some aspects
        assert isinstance(data["aspects"], list)
