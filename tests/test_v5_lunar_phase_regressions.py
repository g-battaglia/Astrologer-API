"""Independent lunar dates and JSON/XML agreement across all four endpoints."""

from datetime import datetime, timezone
from xml.etree import ElementTree

import pytest

# USNO Universal Time, rounded to minutes. Allow 60 seconds for the tabulated
# rounding and small ephemeris/time-scale differences.
# https://aa.usno.navy.mil/api/moon/phases/date?date=1993-09-01&nump=12
# https://aa.usno.navy.mil/api/moon/phases/date?date=2024-05-01&nump=12
# https://aa.usno.navy.mil/api/moon/phases/date?date=2026-09-01&nump=12
WINDOWS = [
    (
        "1993-10-10T11:12:00+00:00",
        24,
        {
            "new_moon": ("1993-09-16T03:10", "1993-10-15T11:36"),
            "first_quarter": ("1993-09-22T19:32", "1993-10-22T08:52"),
            "full_moon": ("1993-09-30T18:54", "1993-10-30T12:38"),
            "last_quarter": ("1993-10-08T19:35", "1993-11-07T06:36"),
        },
    ),
    (
        "2024-06-01T12:30:00+00:00",
        24,
        {
            "new_moon": ("2024-05-08T03:22", "2024-06-06T12:38"),
            "first_quarter": ("2024-05-15T11:48", "2024-06-14T05:18"),
            "full_moon": ("2024-05-23T13:53", "2024-06-22T01:08"),
            "last_quarter": ("2024-05-30T17:13", "2024-06-28T21:53"),
        },
    ),
    (
        "2026-09-29T18:51:02+00:00",
        19,
        {
            "new_moon": ("2026-09-11T03:27", "2026-10-10T15:50"),
            "first_quarter": ("2026-09-18T20:44", "2026-10-18T16:12"),
            "full_moon": ("2026-09-26T16:49", "2026-10-26T04:12"),
            "last_quarter": ("2026-09-04T07:51", "2026-10-03T13:25"),
        },
    ),
]


@pytest.mark.parametrize(
    "reference,age,expected", WINDOWS, ids=("1993", "2024", "2026")
)
@pytest.mark.parametrize(
    "endpoint",
    (
        "/api/v5/moon-phase",
        "/api/v5/moon-phase/context",
        "/api/v5/moon-phase/now-utc",
        "/api/v5/moon-phase/now-utc/context",
    ),
)
def test_lunar_dates_age_and_context(
    client, monkeypatch, reference, age, expected, endpoint
):
    instant = datetime.fromisoformat(reference)
    monkeypatch.setattr("app.routers.moon_phase.get_time_from_google", lambda: instant)
    payload = (
        {}
        if "/now-utc" in endpoint
        else {
            "year": instant.year,
            "month": instant.month,
            "day": instant.day,
            "hour": instant.hour,
            "minute": instant.minute,
            "second": instant.second,
            "latitude": 51.5074,
            "longitude": -0.1276,
            "timezone": "Etc/UTC",
        }
    )
    response = client.post(endpoint, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OK"
    moon = body["moon_phase_overview"]["moon"]
    assert moon["age_days"] == age
    windows = moon["detailed"]["upcoming_phases"]
    for phase, instants in expected.items():
        for direction, date in zip(("last", "next"), instants):
            timestamp = int(windows[phase][direction]["timestamp"])
            expected_time = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
            assert abs(timestamp - expected_time.timestamp()) < 60
            assert (
                (timestamp <= instant.timestamp())
                if direction == "last"
                else (timestamp > instant.timestamp())
            )

    if endpoint.endswith("/context"):
        root = ElementTree.fromstring(body["context"])
        assert root.findtext("moon/age_days") == str(age)
        for phase, window in windows.items():
            for direction, event in window.items():
                node = root.find(f"moon/detailed/upcoming_phases/{phase}/{direction}")
                assert node is not None
                assert node.attrib == {
                    key: str(value) for key, value in event.items() if value is not None
                }
