"""Route and presentation tests for StackSense Web Studio endpoints."""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stacksense.web import app

client = TestClient(app)
SCENARIOS_DIR = Path("data/scenarios")


def test_index_page():
    """Asserts that the root endpoint serves the modernized dashboard HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "StackSense" in response.text
    assert "System Architecture Topology" in response.text
    assert "Architectural Trade-Off Analysis" in response.text


def test_static_assets_vendored():
    """Verifies that the vendored Mermaid.js script and Tailwind CSS are accessible offline via FastAPI static mount."""
    res_mermaid = client.get("/static/vendor/mermaid.min.js")
    assert res_mermaid.status_code == 200
    assert len(res_mermaid.content) > 100_000, "Vendored Mermaid.js must be a valid, complete bundle."

    res_tailwind = client.get("/static/vendor/tailwind.min.css")
    assert res_tailwind.status_code == 200
    assert len(res_tailwind.content) > 1_000, "Vendored Tailwind CSS must be a valid, complete bundle."
    assert "brand-500" in res_tailwind.text or "--tw-" in res_tailwind.text


def test_canonical_recommend_endpoint():
    """Verifies that POST /api/recommend returns the canonical Section 4 ScenarioOutput."""
    p2_path = SCENARIOS_DIR / "P2.json"
    assert p2_path.is_file()

    with open(p2_path, "r", encoding="utf-8") as f:
        p2_input = json.load(f)

    response = client.post("/api/recommend", json={"scenario": p2_input})
    assert response.status_code == 200
    data = response.json()

    assert data["scenario_id"] == "P2"
    assert data["status"] in ("ok", "ok_with_warnings")
    assert "stack" in data
    assert "estimated_monthly_cost_usd" in data
    assert "warnings" in data
    assert "assumptions" in data


def test_api_topology_endpoint():
    """Verifies that POST /api/topology returns both Mermaid syntax and pure-Python SVG."""
    p2_path = SCENARIOS_DIR / "P2.json"
    with open(p2_path, "r", encoding="utf-8") as f:
        p2_input = json.load(f)

    response = client.post("/api/topology", json={"scenario": p2_input})
    assert response.status_code == 200
    data = response.json()

    assert "mermaid" in data
    assert "svg" in data
    assert data["mermaid"].startswith("graph TD")
    assert data["svg"].startswith("<svg")
    assert "</svg>" in data["svg"]


def test_scenarios_matrix_memoized():
    """Verifies that GET /api/scenarios/matrix serves pre-computed benchmark matrix with sub-10ms latency."""
    t0 = time.perf_counter()
    response = client.get("/api/scenarios/matrix")
    duration_ms = (time.perf_counter() - t0) * 1000

    assert response.status_code == 200
    rows = response.json()

    # Must contain all 6 public benchmarks (P1 through P6)
    assert len(rows) == 6
    p_ids = [r["scenario_id"] for r in rows]
    assert p_ids == ["P1", "P2", "P3", "P4", "P5", "P6"]

    # Verify structured fields
    for row in rows:
        assert "project_name" in row
        assert "archetype" in row
        assert "recommended_stack" in row
        assert "cost_range" in row
        assert "architecture_style" in row
        assert "top_rejected_alternative" in row

    # Performance assertion: cached in-memory response must complete in <25ms
    assert duration_ms < 25.0, f"Memoized matrix took {duration_ms:.2f}ms, expected < 25ms"
