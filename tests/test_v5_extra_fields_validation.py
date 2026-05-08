"""
Tests for extra field validation and error message enrichment.

Verifies that:
1. Requests with extra fields return 422 Unprocessable Entity
2. Error messages include helpful suggestions for known field corrections
3. Valid requests (without extra fields) continue to work
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

import pytest
from fastapi.testclient import TestClient


# Valid subject template for testing
VALID_SUBJECT: Dict[str, object] = {
    "name": "Validation Test Subject",
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "longitude": -72.5198761,
    "latitude": 42.3731948,
    "city": "Amherst, Massachusetts",
    "nation": "US",
    "timezone": "America/New_York",
}


class TestExtraFieldsRejection:
    """Tests for rejection of extra/unknown fields in requests."""

    def test_extra_field_in_subject_returns_422(self, client: TestClient) -> None:
        """Extra fields in subject should return 422 error."""
        payload = {"subject": {**deepcopy(VALID_SUBJECT), "unknown_field": "value"}}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "ERROR"
        assert "errors" in body
        assert any("unknown_field" in str(error) for error in body["errors"])

    def test_country_field_suggests_nation(self, client: TestClient) -> None:
        """Using 'country' instead of 'nation' should suggest the correction."""
        subject_with_country = deepcopy(VALID_SUBJECT)
        subject_with_country["country"] = "United States"
        payload = {"subject": subject_with_country}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "ERROR"

        # Check that the error message suggests 'nation' as correction
        error_messages = [str(error.get("msg", "")) for error in body.get("errors", [])]
        assert any("nation" in msg for msg in error_messages), f"Expected 'nation' suggestion in {error_messages}"

    def test_state_field_suggests_city(self, client: TestClient) -> None:
        """Using 'state' field should suggest including it in 'city'."""
        subject_with_state = deepcopy(VALID_SUBJECT)
        subject_with_state["state"] = "Massachusetts"
        payload = {"subject": subject_with_state}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "ERROR"

        # Check that the error message suggests 'city' as correction
        error_messages = [str(error.get("msg", "")) for error in body.get("errors", [])]
        assert any("city" in msg for msg in error_messages), f"Expected 'city' suggestion in {error_messages}"

    def test_house_system_field_suggests_houses_system_identifier(self, client: TestClient) -> None:
        """Using 'house_system' should suggest 'houses_system_identifier'."""
        subject_with_house_system = deepcopy(VALID_SUBJECT)
        subject_with_house_system["house_system"] = "K"
        payload = {"subject": subject_with_house_system}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()

        error_messages = [str(error.get("msg", "")) for error in body.get("errors", [])]
        assert any("houses_system_identifier" in msg for msg in error_messages), f"Expected 'houses_system_identifier' suggestion in {error_messages}"

    def test_lat_lng_fields_suggest_full_names(self, client: TestClient) -> None:
        """Using 'lat' and 'lng' should suggest 'latitude' and 'longitude'."""
        subject_with_short_coords = deepcopy(VALID_SUBJECT)
        subject_with_short_coords["lat"] = 42.37
        subject_with_short_coords["lng"] = -72.52
        payload = {"subject": subject_with_short_coords}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()

        error_messages = [str(error.get("msg", "")) for error in body.get("errors", [])]
        assert any("latitude" in msg for msg in error_messages), f"Expected 'latitude' suggestion in {error_messages}"
        assert any("longitude" in msg for msg in error_messages), f"Expected 'longitude' suggestion in {error_messages}"


class TestValidRequestsStillWork:
    """Ensure valid requests without extra fields continue to work."""

    def test_valid_subject_request_succeeds(self, client: TestClient) -> None:
        """A properly formatted request should succeed."""
        payload = {"subject": deepcopy(VALID_SUBJECT)}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "OK"
        assert "subject" in body

    def test_valid_birth_chart_request_succeeds(self, client: TestClient) -> None:
        """Birth chart with valid subject should succeed."""
        payload = {"subject": deepcopy(VALID_SUBJECT)}

        response = client.post("/api/v5/chart-data/birth-chart", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "OK"


class TestMultipleExtraFields:
    """Test behavior when multiple extra fields are sent."""

    def test_multiple_extra_fields_all_reported(self, client: TestClient) -> None:
        """All extra fields should be reported in the error response."""
        subject_with_multiple_extras = deepcopy(VALID_SUBJECT)
        subject_with_multiple_extras["country"] = "US"
        subject_with_multiple_extras["state"] = "Massachusetts"
        subject_with_multiple_extras["unknown"] = "value"
        payload = {"subject": subject_with_multiple_extras}

        response = client.post("/api/v5/subject", json=payload)

        assert response.status_code == 422
        body = response.json()
        errors = body.get("errors", [])

        # All three extra fields should be mentioned
        all_errors_str = str(errors)
        assert "country" in all_errors_str
        assert "state" in all_errors_str
        assert "unknown" in all_errors_str


class TestExtraFieldsInDifferentModels:
    """Test extra field rejection across different request types."""

    def test_extra_field_in_synastry_first_subject(self, client: TestClient) -> None:
        """Extra fields in synastry first_subject should be rejected."""
        payload = {
            "first_subject": {**deepcopy(VALID_SUBJECT), "extra": "value"},
            "second_subject": deepcopy(VALID_SUBJECT),
        }
        payload["second_subject"]["name"] = "Second Subject"

        response = client.post("/api/v5/chart-data/synastry", json=payload)

        assert response.status_code == 422

    def test_extra_field_in_transit_subject_ignored(self, client: TestClient) -> None:
        """Extra fields in transit_subject should be silently ignored."""
        transit_subject = {
            "year": 2025,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "longitude": -72.52,
            "latitude": 42.37,
            "city": "Amherst",
            "timezone": "America/New_York",
            "extra_field": "not allowed",
        }
        payload = {
            "first_subject": deepcopy(VALID_SUBJECT),
            "transit_subject": transit_subject,
        }

        response = client.post("/api/v5/chart-data/transit", json=payload)

        assert response.status_code == 200

    def test_extra_field_at_request_level(self, client: TestClient) -> None:
        """Extra fields at the request body level should be rejected."""
        payload = {
            "subject": deepcopy(VALID_SUBJECT),
            "not_a_valid_option": True,
        }

        response = client.post("/api/v5/chart-data/birth-chart", json=payload)

        assert response.status_code == 422
