"""Validate the literal RapidAPI bodies before backend alias normalization."""

from copy import deepcopy
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from scripts import generate_rapidapi_docs as generator
from tests.conftest import assert_api_svg_valid


@pytest.fixture
def catalogue():
    return generator.load_openapi(), generator.load_all_markdown_docs()


def test_all_28_published_request_examples_match_openapi(catalogue):
    spec, docs = catalogue
    assert len(docs) == 28
    assert {doc["endpoint"] for doc in docs} == set(generator.ENDPOINT_ORDER)
    generator.validate_request_examples(spec, docs)


def test_lunar_response_examples_match_verified_fixtures(catalogue):
    _, docs = catalogue
    for doc in docs:
        if "/moon-phase" not in doc["endpoint"]:
            continue
        name = "moon_phase_now_utc" if "/now-utc" in doc["endpoint"] else "moon_phase"
        fixture = json.loads(
            (Path(__file__).parent / "baselines" / f"{name}.json").read_text()
        )
        expected = fixture["moon_phase_overview"]["moon"]
        example = doc["response_example"]["moon_phase_overview"]["moon"]
        assert example["age_days"] == expected["age_days"]
        assert (
            example["detailed"]["upcoming_phases"]
            == expected["detailed"]["upcoming_phases"]
        )


@pytest.mark.parametrize("alias", ("Lilith", "north_node"))
def test_backend_aliases_are_rejected_in_published_examples(catalogue, alias):
    spec, docs = catalogue
    birth = next(doc for doc in docs if doc["endpoint"] == "/api/v5/chart/birth-chart")
    birth["request_example"]["active_points"][0] = alias
    with pytest.raises(ValueError, match="active_points"):
        generator.validate_request_examples(spec, docs)


@pytest.mark.parametrize(
    "fault",
    ("required", "range", "missing_example", "unknown", "duplicate", "missing_doc"),
)
def test_invalid_catalogue_fails_before_generation(catalogue, fault):
    spec, docs = catalogue
    birth = next(doc for doc in docs if doc["endpoint"] == "/api/v5/chart/birth-chart")
    if fault == "required":
        del birth["request_example"]["subject"]
    elif fault == "range":
        birth["request_example"]["subject"]["month"] = 13
    elif fault == "missing_example":
        birth["request_example"] = None
    elif fault == "unknown":
        birth["endpoint"] = "/api/v5/unknown"
    elif fault == "duplicate":
        docs.append(deepcopy(birth))
    else:
        docs.remove(birth)
    with pytest.raises(ValueError):
        generator.validate_request_examples(spec, docs)


def test_malformed_request_json_reports_source(tmp_path):
    doc = tmp_path / "Broken.md"
    doc.write_text(
        '## Endpoint\n/api/v5/subject\n## Name\nSubject\n## Request Body Example\n```json\n{"subject":}\n```\n'
    )
    with pytest.raises(ValueError, match="Broken.md.*Invalid JSON"):
        generator.parse_markdown_file(doc)


def test_check_does_not_write_or_modify_output(monkeypatch, tmp_path):
    output = tmp_path / "rapidapi.json"
    output.write_text("previous catalogue")
    monkeypatch.setattr(generator, "OUTPUT_FILE", output)
    generator.main(["--check"])
    assert output.read_text() == "previous catalogue"


def test_invalid_example_preserves_existing_output(catalogue, monkeypatch, tmp_path):
    spec, docs = catalogue
    docs[0]["request_example"] = None
    output = tmp_path / "rapidapi.json"
    output.write_text("previous catalogue")
    monkeypatch.setattr(generator, "OUTPUT_FILE", output)
    monkeypatch.setattr(generator, "load_openapi", lambda: spec)
    monkeypatch.setattr(generator, "load_all_markdown_docs", lambda: docs)
    with pytest.raises(ValueError):
        generator.main([])
    assert output.read_text() == "previous catalogue"


@pytest.mark.parametrize("endpoint", generator.ENDPOINT_ORDER)
def test_every_published_example_runs_and_returns_valid_content(
    client, catalogue, endpoint
):
    spec, docs = catalogue
    doc = next(doc for doc in docs if doc["endpoint"] == endpoint)
    response = client.post(endpoint, json=deepcopy(doc["request_example"]))
    assert response.status_code == 200, response.text[:500]
    body = response.json()
    assert body["status"] == "OK"
    assert set(doc["response_example"]) <= set(body)
    if "chart" in body:
        assert_api_svg_valid(body["chart"])
    if "context" in body:
        assert body["context"].strip()
        ElementTree.fromstring(body["context"])
