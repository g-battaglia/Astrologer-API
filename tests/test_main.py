"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from sys import path
from pathlib import Path

path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timezone

client = TestClient(app)


def test_status():
    """
    Tests if the status endpoint returns the correct status.
    """

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_get_now():
    """
    Tests if the now function returns the correct utm time.
    """

    now = datetime.now(timezone.utc)
    response = client.get("/api/v4/now")

    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert response.json()["data"]["name"] == "Now"
    assert response.json()["data"]["year"] == now.year
    assert response.json()["data"]["month"] == now.month
    assert response.json()["data"]["day"] == now.day
    assert response.json()["data"]["minute"] == now.minute


def test_birth_data():
    """Test if the birth data is returned correctly"""

    response = client.post(
        "/api/v4/birth-data",
        json={
            "subject": {
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
                "language": "IT",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "OK"

    assert response.json()["data"]["nation"] == "IT"

    assert response.json()["data"]["sun"]["name"] == "Sun"
    assert response.json()["data"]["sun"]["quality"] == "Mutable"
    assert response.json()["data"]["sun"]["element"] == "Air"
    assert response.json()["data"]["sun"]["sign"] == "Gem"
    assert response.json()["data"]["sun"]["sign_num"] == 2
    assert round(response.json()["data"]["sun"]["position"]) == 25
    assert round(response.json()["data"]["sun"]["abs_pos"]) == 85
    assert response.json()["data"]["sun"]["emoji"] == "♊️"
    assert response.json()["data"]["sun"]["house"] == "Eleventh_House"
    assert response.json()["data"]["sun"]["retrograde"] == False
    assert response.json()["data"]["sun"]["point_type"] == "Planet"

    assert response.json()["data"]["lunar_phase"]["moon_emoji"] == "🌖"


def test_relationship_score():
    """
    Tests if the relationship score is returned correctly
    """

    response = client.post(
        "/api/v4/relationship-score",
        json={
            "first_subject": {
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
                "language": "IT",
            },
            "second_subject": {
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
                "language": "IT",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert response.json()["score"] == 24


def test_birth_chart():
    """
    Tests if the birth chart is returned correctly
    """

    response = client.post(
        "/api/v4/birth-chart",
        json={
            "subject": {
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
        },
    )

    # ------------------
    # Status
    # ------------------

    assert response.status_code == 200
    assert response.json()["status"] == "OK"

    # ------------------
    # Data
    # ------------------

    ## Sun
    assert response.json()["data"]["sun"]["name"] == "Sun"
    assert response.json()["data"]["sun"]["quality"] == "Mutable"
    assert response.json()["data"]["sun"]["element"] == "Fire"
    assert response.json()["data"]["sun"]["sign"] == "Sag"
    assert response.json()["data"]["sun"]["sign_num"] == 8
    assert round(response.json()["data"]["sun"]["position"]) == 21
    assert round(response.json()["data"]["sun"]["abs_pos"]) == 261
    assert response.json()["data"]["sun"]["emoji"] == "♐️"
    assert response.json()["data"]["sun"]["point_type"] == "Planet"
    assert response.json()["data"]["sun"]["house"] == "Ninth_House"
    assert response.json()["data"]["sun"]["retrograde"] == False

    ## Moon Phase
    assert round(response.json()["data"]["lunar_phase"]["degrees_between_s_m"]) == 58
    assert response.json()["data"]["lunar_phase"]["moon_phase"] == 5
    assert response.json()["data"]["lunar_phase"]["sun_phase"] == 4
    assert response.json()["data"]["lunar_phase"]["moon_emoji"] == "🌒"

    # ------------------
    # Chart
    # ------------------

    assert type(response.json()["chart"]) == str

    # ------------------
    # Aspects
    # ------------------

    assert response.json()["aspects"][0]["p1_name"] == "Sun"
    assert round(response.json()["aspects"][0]["p1_abs_pos"]) == 261
    assert response.json()["aspects"][0]["p2_name"] == "Moon"
    assert round(response.json()["aspects"][0]["p2_abs_pos"]) == 318
    assert response.json()["aspects"][0]["aspect"] == "sextile"
    assert round(response.json()["aspects"][0]["orbit"]) == -2
    assert response.json()["aspects"][0]["aspect_degrees"] == 60
    assert round(response.json()["aspects"][0]["diff"]) == 58
    assert response.json()["aspects"][0]["p1"] == 0
    assert response.json()["aspects"][0]["p2"] == 1
