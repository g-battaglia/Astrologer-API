"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from sys import path
from pathlib import Path

path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_now_utm():
    """
    Tests if the now function returns the correct utm time.
    """

    response = client.get("/api/v3/now")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert response.json()["data"]["name"] == "Now"


def test_get_city_data():
    """Tests if the city data is returned correctly"""

    response = client.post("/api/v1/city-data", json={"city": "Roma", "country": "IT"})

    assert response.status_code == 200
    assert response.json()["data"][0] == {
        "name": "Roma",
        "lat": "41.89193",
        "lng": "12.51133",
        "country": "Italy",
        "country_code": "IT",
        "admin_name": "07",
        "name_located": "Roma, Lazio",
    }


def test_birth_data():
    """Test if the birth data is returned correctly"""

    response = client.post(
        "/api/v3/birth-data",
        json={
            "name": "FastAPI Unit Test",
            "year": 1946,
            "month": 6,
            "day": 16,
            "hour": 10,
            "minute": 10,
            "longitude": 12.4963655,
            "latitude": 41.9027835,
            "city": "Roma",
            "timezone": "Europe/Rome",
            "language": "IT",
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "OK"

    assert response.json()["data"]["sun"] == {
        "name": "Sun",
        "quality": "Mutable",
        "element": "Air",
        "sign": "Gem",
        "sign_num": 2,
        "position": 24.56961027710318,
        "abs_pos": 84.56961027710318,
        "emoji": "♊️",
        "house": "Eleventh House",
        "retrograde": False,
        "point_type": "Planet",
    }

    assert response.json()["data"]["lunar_phase"]["moon_emoji"] == "🌖"


def test_birth_chart():
    """Test if the birth chart is returned correctly"""

    response = client.post(
        "/api/v3/birth-chart",
        json={
            "name": "FastAPI Unit Test",
            "year": 1946,
            "month": 6,
            "day": 16,
            "hour": 10,
            "minute": 10,
            "longitude": 12.4963655,
            "latitude": 41.9027835,
            "city": "Roma",
            "timezone": "Europe/Rome",
            "language": "IT",
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "OK"

    assert response.json()["data"]["sun"] == {
        "name": "Sun",
        "quality": "Mutable",
        "element": "Air",
        "sign": "Gem",
        "sign_num": 2,
        "position": 24.56961027710318,
        "abs_pos": 84.56961027710318,
        "emoji": "♊️",
        "house": "Eleventh House",
        "retrograde": False,
        "point_type": "Planet",
    }

    print(response.json()["aspects"][0])

    assert response.json()["aspects"][0] == {
        "p1_name": "Sun",
        "p1_abs_pos": 84.56961027710318,
        "p2_name": "Mars",
        "p2_abs_pos": 147.73760991657213,
        "aspect": "sextile",
        "orbit": 3.167999639468917,
        "aspect_degrees": 60,
        "color": "#d59e28",
        "aid": 3,
        "diff": 63.167999639468945,
        "p1": 0,
        "p2": 4,
    }

    print(response.json()["chart"][:5])

    assert response.json()["chart"][:5] == "<?xml"


def test_get_discepolo_score():
    """
    Tests if Discepolo"s score is returned correctly.
    """

    response = client.post(
        "/api/v3/discepolo-score",
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
                "timezone": "Europe/Rome",
                "language": "IT",
            },
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "OK"

    assert response.json()["score"] == 40


if __name__ == "__main__":
    test_now_utm()
    test_get_city_data()
    test_birth_data()
    test_birth_chart()
    test_get_discepolo_score()
