"""
Configurazione test condivisa e minimale.

Obiettivi:
- Esporre un `client` FastAPI riutilizzabile.
- Congelare il tempo usato dagli endpoint `now/*` per risultati deterministici.
- Supportare il flag --update-baselines per rigenerare i file di snapshot.

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


# ---------------------------------------------------------------------------
# Opzioni CLI custom per pytest
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Rigenera i file baseline in tests/baselines/ invece di confrontarli.",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Client FastAPI riutilizzabile per i test di integrazione sugli endpoint."""
    return TestClient(app)


@pytest.fixture(scope="session")
def update_baselines(request: pytest.FixtureRequest) -> bool:
    """True quando pytest viene lanciato con --update-baselines."""
    return request.config.getoption("--update-baselines")


@pytest.fixture(scope="session")
def baselines_dir() -> Path:
    """Directory dove risiedono i file baseline JSON."""
    d = Path(__file__).parent / "baselines"
    d.mkdir(exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# SVG Validation Helper
# ---------------------------------------------------------------------------


def assert_api_svg_valid(svg: str, *, expect_css_variables: bool = True) -> None:
    """Validate that an SVG string returned by the API is well-formed.

    This is the primary guard against SVG regressions:
    - Attribute merging during minification (``<svgxmlns=...``)
    - Missing namespace declarations
    - Malformed XML from incorrect string processing
    - Accidental removal of CSS custom properties

    Args:
        svg: The SVG string to validate.
        expect_css_variables: When True (default), assert that CSS custom
            properties (``var(--…)``) and a ``<style>`` block are present.
    """
    from xml.etree import ElementTree

    assert isinstance(svg, str), f"SVG must be a string, got {type(svg).__name__}"
    assert len(svg) > 100, f"SVG suspiciously short ({len(svg)} chars)"

    # XML well-formedness — catches attribute merging, broken tags, etc.
    try:
        tree = ElementTree.fromstring(svg)
    except ElementTree.ParseError as exc:
        preview = svg[:500]
        raise AssertionError(
            f"API returned invalid XML in chart SVG: {exc}\nFirst 500 chars:\n{preview}"
        ) from exc

    # Root element must be <svg>
    local_name = tree.tag.rsplit("}", 1)[-1] if "}" in tree.tag else tree.tag
    assert local_name == "svg", f"Expected <svg> root element, got <{local_name}>"

    # Namespace
    assert (
        "http://www.w3.org/2000/svg" in tree.tag
        or tree.attrib.get("xmlns") == "http://www.w3.org/2000/svg"
    ), "SVG must declare xmlns='http://www.w3.org/2000/svg'"

    # Anti-regression: attribute merging
    assert "<svgxmlns" not in svg, (
        "SVG tag name merged with attributes — minification is broken"
    )

    # CSS custom properties
    if expect_css_variables:
        assert "var(--" in svg, (
            "SVG must contain CSS custom properties for consumer restyling"
        )
        assert "<style" in svg, (
            "SVG must contain a <style> block with CSS variable definitions"
        )


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
