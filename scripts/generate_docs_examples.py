import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Use test config to bypass auth middleware (debug=true skips SecretKeyCheckerMiddleware)
os.environ["ENV_TYPE"] = "test"

from fastapi.testclient import TestClient
from app.main import app

EXAMPLES_DIR = Path("docs/examples")
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def save_example(
    filename, title, endpoint, request_body, response_body, fm_title, fm_description
):
    filepath = EXAMPLES_DIR / filename
    with open(filepath, "w") as f:
        # Write YAML frontmatter
        f.write("---\n")
        f.write(f"title: '{fm_title}'\n")
        f.write(f"description: '{fm_description}'\n")
        f.write("---\n\n")

        f.write(f"# {title}\n\n")
        f.write(f"Endpoint: `{endpoint}`\n\n")

        f.write("## Request Body\n")
        f.write("```json\n")
        f.write(json.dumps(request_body, indent=2))
        f.write("\n```\n\n")

        f.write("## Response Body\n")
        f.write("```json\n")
        if isinstance(response_body, dict):
            f.write(json.dumps(response_body, indent=2))
        else:
            # Handle non-dict responses if any (though most are JSON)
            f.write(str(response_body))
        f.write("\n```\n")
    print(f"Generated {filepath}")


def generate_examples():
    client = TestClient(app)

    # 1. Subject
    subject_payload = {
        "subject": {
            "name": "John Doe",
            "year": 1990,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 30,
            "city": "London",
            "nation": "GB",
            "longitude": -0.1278,
            "latitude": 51.5074,
            "timezone": "Europe/London",
            "zodiac_type": "Tropical",
            "houses_system_identifier": "P",
        }
    }
    resp = client.post("/api/v5/subject", json=subject_payload)
    save_example(
        "subject.md",
        "Subject Data Example",
        "/api/v5/subject",
        subject_payload,
        resp.json(),
        fm_title="Subject JSON Data Example",
        fm_description="JSON example of a calculated astrological subject. Shows the result of raw birth data processed through high-precision ephemeris engines.",
    )

    # 2. Compatibility Score
    comp_payload = {
        "first_subject": {
            "name": "Partner A",
            "year": 1990,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "city": "London",
            "nation": "GB",
            "longitude": -0.1278,
            "latitude": 51.5074,
            "timezone": "Europe/London",
        },
        "second_subject": {
            "name": "Partner B",
            "year": 1992,
            "month": 5,
            "day": 15,
            "hour": 18,
            "minute": 30,
            "city": "New York",
            "nation": "US",
            "longitude": -74.006,
            "latitude": 40.7128,
            "timezone": "America/New_York",
        },
    }
    resp = client.post("/api/v5/compatibility-score", json=comp_payload)
    save_example(
        "compatibility_score.md",
        "Compatibility Score Example",
        "/api/v5/compatibility-score",
        comp_payload,
        resp.json(),
        fm_title="Compatibility Score JSON Example",
        fm_description="Example response for the Compatibility Score endpoint. Shows numerical scores, qualitative descriptions, and inter-aspect data for synastry.",
    )

    # 3. Natal Chart Data
    natal_data_payload = {
        "subject": subject_payload["subject"],
        "distribution_method": "weighted",
    }
    resp = client.post("/api/v5/chart-data/birth-chart", json=natal_data_payload)
    save_example(
        "natal_chart_data.md",
        "Natal Chart Data Example",
        "/api/v5/chart-data/birth-chart",
        natal_data_payload,
        resp.json(),
        fm_title="Natal Chart JSON Data Example",
        fm_description="Example JSON response for full natal calculations. Structure of machine-readable data for planets, houses, and aspects in a birth chart.",
    )

    # 4. Natal Chart SVG
    # Note: SVG strings can be long, but we want complete examples.
    natal_chart_payload = {
        "subject": subject_payload["subject"],
        "theme": "classic",
        "split_chart": False,
    }
    resp = client.post("/api/v5/chart/birth-chart", json=natal_chart_payload)
    save_example(
        "natal_chart_svg.md",
        "Natal Chart SVG Example",
        "/api/v5/chart/birth-chart",
        natal_chart_payload,
        resp.json(),
        fm_title="Natal Chart SVG Example",
        fm_description="Sample SVG output for a professional birth chart. High-quality visualization of natal planetary placements, houses, and aspect patterns.",
    )

    # 5. Now Subject
    now_subject_payload = {
        "name": "Current Sky",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P",
    }
    resp = client.post("/api/v5/now/subject", json=now_subject_payload)
    save_example(
        "now_subject.md",
        "Now Subject Example",
        "/api/v5/now/subject",
        now_subject_payload,
        resp.json(),
        fm_title="Now Subject JSON Example",
        fm_description="Example JSON output for real-time subject data. Demonstrates the structure of astrological data calculated for the current moment.",
    )

    # 6. Synastry Chart Data
    synastry_data_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
        "include_house_comparison": True,
        "include_relationship_score": True,
    }
    resp = client.post("/api/v5/chart-data/synastry", json=synastry_data_payload)
    save_example(
        "synastry_chart_data.md",
        "Synastry Chart Data Example",
        "/api/v5/chart-data/synastry",
        synastry_data_payload,
        resp.json(),
        fm_title="Synastry Chart JSON Data Example",
        fm_description="Example JSON response for relationship compatibility calculations. Highlights inter-axial and inter-planetary aspects between two subjects.",
    )

    # 7. Composite Chart Data
    composite_data_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
    }
    resp = client.post("/api/v5/chart-data/composite", json=composite_data_payload)
    save_example(
        "composite_chart_data.md",
        "Composite Chart Data Example",
        "/api/v5/chart-data/composite",
        composite_data_payload,
        resp.json(),
        fm_title="Composite Chart JSON Data Example",
        fm_description="JSON example for Composite Chart data. Structure of midpoint calculations representing the unique essence of a partnership.",
    )

    # 8. Transit Chart Data
    transit_data_payload = {
        "first_subject": subject_payload["subject"],
        "transit_subject": {
            "name": "Transit Moment",
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "city": "London",
            "nation": "GB",
            "longitude": -0.1278,
            "latitude": 51.5074,
            "timezone": "Europe/London",
        },
    }
    resp = client.post("/api/v5/chart-data/transit", json=transit_data_payload)
    save_example(
        "transit_chart_data.md",
        "Transit Chart Data Example",
        "/api/v5/chart-data/transit",
        transit_data_payload,
        resp.json(),
        fm_title="Transit Chart JSON Data Example",
        fm_description="Example JSON response for Transit Chart Data. Highlights the structure of transit-to-natal aspect calculations and planetary positions.",
    )

    # 9. Solar Return Chart Data
    solar_return_data_payload = {
        "subject": subject_payload["subject"],
        "year": 2024,
        "wheel_type": "dual",
    }
    resp = client.post(
        "/api/v5/chart-data/solar-return", json=solar_return_data_payload
    )
    save_example(
        "solar_return_chart_data.md",
        "Solar Return Chart Data Example",
        "/api/v5/chart-data/solar-return",
        solar_return_data_payload,
        resp.json(),
        fm_title="Solar Return JSON Data Example",
        fm_description="JSON example for Solar Return data. Structure of calculations for the exact moment of the annual solar return for predictive astrology.",
    )

    # 10. Lunar Return Chart Data
    lunar_return_data_payload = {
        "subject": subject_payload["subject"],
        "year": 2024,
        "month": 5,
        "wheel_type": "single",
    }
    resp = client.post(
        "/api/v5/chart-data/lunar-return", json=lunar_return_data_payload
    )
    save_example(
        "lunar_return_chart_data.md",
        "Lunar Return Chart Data Example",
        "/api/v5/chart-data/lunar-return",
        lunar_return_data_payload,
        resp.json(),
        fm_title="Lunar Return JSON Data Example",
        fm_description="JSON example for Lunar Return data. Shows the calculated positions for the natal subject and the return moment for monthly forecasting.",
    )

    # 11. Now Chart SVG
    now_chart_payload = {"name": "Current Sky", "theme": "dark"}
    resp = client.post("/api/v5/now/chart", json=now_chart_payload)
    save_example(
        "now_chart_svg.md",
        "Now Chart SVG Example",
        "/api/v5/now/chart",
        now_chart_payload,
        resp.json(),
        fm_title="Now Chart SVG Example",
        fm_description="View a sample Now chart SVG. Real-time visualization of the current global planetary positions rendered as a professional chart wheel.",
    )

    # 12. Synastry Chart SVG
    synastry_chart_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
        "theme": "classic",
        "split_chart": False,
    }
    resp = client.post("/api/v5/chart/synastry", json=synastry_chart_payload)
    save_example(
        "synastry_chart_svg.md",
        "Synastry Chart SVG Example",
        "/api/v5/chart/synastry",
        synastry_chart_payload,
        resp.json(),
        fm_title="Synastry Chart SVG Example",
        fm_description="View a sample SVG output for the Synastry Chart endpoint. Professional dual-wheel visualization of relationship compatibility and inter-aspects.",
    )

    # 13. Composite Chart SVG
    composite_chart_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
        "theme": "dark",
    }
    resp = client.post("/api/v5/chart/composite", json=composite_chart_payload)
    save_example(
        "composite_chart_svg.md",
        "Composite Chart SVG Example",
        "/api/v5/chart/composite",
        composite_chart_payload,
        resp.json(),
        fm_title="Composite Chart SVG Example",
        fm_description="See a sample SVG composite chart. Visual representation of the relationship as a single entity based on planetary midpoints between partners.",
    )

    # 14. Transit Chart SVG
    transit_chart_payload = {
        "first_subject": subject_payload["subject"],
        "transit_subject": transit_data_payload["transit_subject"],
        "theme": "classic",
    }
    resp = client.post("/api/v5/chart/transit", json=transit_chart_payload)
    save_example(
        "transit_chart_svg.md",
        "Transit Chart SVG Example",
        "/api/v5/chart/transit",
        transit_chart_payload,
        resp.json(),
        fm_title="Transit Chart SVG Example",
        fm_description="SVG example for the Transit Chart endpoint. Professional dual-wheel visualization comparing current planetary movements to a natal foundation.",
    )

    # 15. Solar Return Chart SVG
    solar_return_chart_payload = {
        "subject": subject_payload["subject"],
        "year": 2024,
        "wheel_type": "dual",
        "theme": "classic",
    }
    resp = client.post("/api/v5/chart/solar-return", json=solar_return_chart_payload)
    save_example(
        "solar_return_chart_svg.md",
        "Solar Return Chart SVG Example",
        "/api/v5/chart/solar-return",
        solar_return_chart_payload,
        resp.json(),
        fm_title="Solar Return Chart SVG Example",
        fm_description="Sample SVG output for a Solar Return. Professional dual-wheel visualization for annual birthday forecasting and year-ahead planning.",
    )

    # 16. Lunar Return Chart SVG
    lunar_return_chart_payload = {
        "subject": subject_payload["subject"],
        "year": 2024,
        "month": 5,
        "wheel_type": "single",
        "theme": "classic",
    }
    resp = client.post("/api/v5/chart/lunar-return", json=lunar_return_chart_payload)
    save_example(
        "lunar_return_chart_svg.md",
        "Lunar Return Chart SVG Example",
        "/api/v5/chart/lunar-return",
        lunar_return_chart_payload,
        resp.json(),
        fm_title="Lunar Return Chart SVG Example",
        fm_description="SVG example for the Lunar Return Chart. Visual representation of the monthly emotional cycle based on the Moons return to its natal degree.",
    )

    # 17. Subject Context
    context_payload = {"subject": subject_payload["subject"]}
    resp = client.post("/api/v5/context/subject", json=context_payload)
    save_example(
        "subject_context.md",
        "Subject Context Example",
        "/api/v5/context/subject",
        context_payload,
        resp.json(),
        fm_title="Subject Context JSON Example",
        fm_description="Sample JSON output showing structured astrological context for AI personality insights. Formatted for use as a baseline for LLM-generated readings.",
    )

    # 18. Now Context
    now_context_payload = {"name": "Current Atmosphere"}
    resp = client.post("/api/v5/now/context", json=now_context_payload)
    save_example(
        "now_context.md",
        "Now Context Example",
        "/api/v5/now/context",
        now_context_payload,
        resp.json(),
        fm_title="Now Context JSON Example",
        fm_description="Example JSON response providing real-time astrological context for AI models. Optimized for Current Sky or Vibe Check interpretations.",
    )

    # 19. Natal Chart Context
    natal_context_payload = {"subject": subject_payload["subject"]}
    resp = client.post("/api/v5/context/birth-chart", json=natal_context_payload)
    save_example(
        "natal_context.md",
        "Natal Chart Context Example",
        "/api/v5/context/birth-chart",
        natal_context_payload,
        resp.json(),
        fm_title="Natal Context JSON Example",
        fm_description="Complete JSON example for AI-ready natal chart context. Demonstrates how chart dynamics are summarized for Large Language Models (LLMs).",
    )

    # 20. Synastry Context
    synastry_context_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
    }
    resp = client.post("/api/v5/context/synastry", json=synastry_context_payload)
    save_example(
        "synastry_context.md",
        "Synastry Context Example",
        "/api/v5/context/synastry",
        synastry_context_payload,
        resp.json(),
        fm_title="Synastry Context JSON Example",
        fm_description="JSON example of relationship context optimized for AI interpretation. Shows synthesized synastry data ready for LLM processing.",
    )

    # 21. Composite Context
    composite_context_payload = {
        "first_subject": comp_payload["first_subject"],
        "second_subject": comp_payload["second_subject"],
    }
    resp = client.post("/api/v5/context/composite", json=composite_context_payload)
    save_example(
        "composite_context.md",
        "Composite Context Example",
        "/api/v5/context/composite",
        composite_context_payload,
        resp.json(),
        fm_title="Composite Context JSON Example",
        fm_description="Sample composite chart context in JSON format. Provides the structural entity context required for AI-powered relationship destiny insights.",
    )

    # 22. Transit Context
    transit_context_payload = {
        "first_subject": subject_payload["subject"],
        "transit_subject": transit_data_payload["transit_subject"],
    }
    resp = client.post("/api/v5/context/transit", json=transit_context_payload)
    save_example(
        "transit_context.md",
        "Transit Context Example",
        "/api/v5/context/transit",
        transit_context_payload,
        resp.json(),
        fm_title="Transit Context JSON Example",
        fm_description="Example JSON output for transit context designed for AI narratives. Highlights how current planetary influences are summarized for LLM analysis.",
    )

    # 23. Solar Return Context
    solar_return_context_payload = {"subject": subject_payload["subject"], "year": 2024}
    resp = client.post(
        "/api/v5/context/solar-return", json=solar_return_context_payload
    )
    save_example(
        "solar_return_context.md",
        "Solar Return Context Example",
        "/api/v5/context/solar-return",
        solar_return_context_payload,
        resp.json(),
        fm_title="Solar Return Context JSON Example",
        fm_description="Formatted JSON example of Solar Return context for AI forecasting. Provides the thematic summaries for LLM predictive readings.",
    )

    # 24. Lunar Return Context
    lunar_return_context_payload = {
        "subject": subject_payload["subject"],
        "year": 2024,
        "month": 5,
    }
    resp = client.post(
        "/api/v5/context/lunar-return", json=lunar_return_context_payload
    )
    save_example(
        "lunar_return_context.md",
        "Lunar Return Context Example",
        "/api/v5/context/lunar-return",
        lunar_return_context_payload,
        resp.json(),
        fm_title="Lunar Return Context JSON Example",
        fm_description="Sample JSON response for Lunar Return context optimized for AI cycles. Provides structured emotional themes for LLM monthly outlooks.",
    )

    # 25. Moon Phase
    moon_phase_payload = {
        "year": 1993,
        "month": 10,
        "day": 10,
        "hour": 12,
        "minute": 12,
        "second": 0,
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timezone": "Europe/London",
    }
    resp = client.post("/api/v5/moon-phase", json=moon_phase_payload)
    save_example(
        "moon_phase.md",
        "Moon Phase Example",
        "/api/v5/moon-phase",
        moon_phase_payload,
        resp.json(),
        fm_title="Moon Phase JSON Example",
        fm_description="Complete JSON example of detailed moon phase data including illumination, upcoming phases, eclipses, and sun position.",
    )

    # 26. Moon Phase Context
    resp = client.post("/api/v5/moon-phase/context", json=moon_phase_payload)
    save_example(
        "moon_phase_context.md",
        "Moon Phase Context Example",
        "/api/v5/moon-phase/context",
        moon_phase_payload,
        resp.json(),
        fm_title="Moon Phase Context JSON Example",
        fm_description="Complete JSON example of moon phase data with AI-optimized XML context for LLM integration.",
    )

    # 27. Moon Phase Now (UTC)
    moon_phase_now_payload = {}
    resp = client.post("/api/v5/moon-phase/now-utc", json=moon_phase_now_payload)
    save_example(
        "moon_phase_now_utc.md",
        "Moon Phase Now (UTC) Example",
        "/api/v5/moon-phase/now-utc",
        moon_phase_now_payload,
        resp.json(),
        fm_title="Moon Phase Now (UTC) JSON Example",
        fm_description="JSON example of real-time moon phase data at Greenwich Observatory. Shows the response structure for the current lunar state.",
    )

    # 28. Moon Phase Now (UTC) Context
    resp = client.post(
        "/api/v5/moon-phase/now-utc/context", json=moon_phase_now_payload
    )
    save_example(
        "moon_phase_now_utc_context.md",
        "Moon Phase Now (UTC) Context Example",
        "/api/v5/moon-phase/now-utc/context",
        moon_phase_now_payload,
        resp.json(),
        fm_title="Moon Phase Now Context (UTC) JSON Example",
        fm_description="Complete JSON example of current moon phase data with AI-optimized XML context at Greenwich.",
    )


if __name__ == "__main__":
    generate_examples()
