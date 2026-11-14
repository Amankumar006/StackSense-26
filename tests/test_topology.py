"""Tests for the architecture topology generation engine (src/stacksense/topology.py)."""

import json
from pathlib import Path

import pytest

from stacksense.engine import RecommendationEngine
from stacksense.models.enums import EngineStatus
from stacksense.models.output import ScenarioOutput
from stacksense.topology import (
    generate_topology_mermaid,
    generate_topology_svg,
    sanitize_node_label,
)

engine = RecommendationEngine()
SCENARIOS_DIR = Path("data/scenarios")


def test_node_label_sanitization():
    """Validates that quotes, brackets, and HTML entities are properly sanitized."""
    raw = 'PostgreSQL ["Managed"] & <Auth0>'
    clean = sanitize_node_label(raw)
    assert '"' not in clean
    assert "[" not in clean
    assert "]" not in clean
    assert "&amp;" in clean
    assert "&lt;" in clean
    assert "&gt;" in clean


def test_topology_defensive_infeasible():
    """Asserts that topology generators gracefully handle stack: None without raising AttributeError."""
    infeasible_output = ScenarioOutput(
        scenario_id="EC-INVASIBLE",
        engine_version="1.0.0",
        status=EngineStatus.INFEASIBLE,
        summary="Contradictory constraints: air-gapped on-premise requirement incompatible with AWS.",
        stack=None,
        warnings=[],
        assumptions=[],
        validation_errors=[],
    )

    # Mermaid check
    mermaid_str = generate_topology_mermaid(infeasible_output)
    assert "graph TD" in mermaid_str
    assert "Infeasible Architecture" in mermaid_str
    assert "AttributeError" not in mermaid_str

    # SVG check
    svg_str = generate_topology_svg(infeasible_output)
    assert "<svg" in svg_str
    assert "Infeasible Architecture Specification" in svg_str
    assert "</svg>" in svg_str


def test_topology_defensive_none_layers():
    """Asserts that static site architectures (e.g. P1 with backend: 'None') do not generate broken nodes."""
    p1_path = SCENARIOS_DIR / "P1.json"
    assert p1_path.is_file(), "P1.json scenario fixture must exist."

    with open(p1_path, "r", encoding="utf-8") as f:
        p1_input = json.load(f)

    output = engine.evaluate_scenario(p1_input)
    assert output.stack is not None
    assert output.stack.backend.choice == "None"

    # Mermaid check
    mermaid_str = generate_topology_mermaid(output, p1_input)
    assert "graph TD" in mermaid_str
    assert "App_Compute" not in mermaid_str  # No backend compute node for static site
    assert "subgraph Clients" in mermaid_str
    assert "subgraph Edge" in mermaid_str

    # SVG check
    svg_str = generate_topology_svg(output, p1_input)
    assert "<svg" in svg_str
    assert "Static Edge Serving" in svg_str
    assert "</svg>" in svg_str


def test_topology_mermaid_all_benchmarks():
    """Verifies that all 6 official scenarios (P1 through P6) generate valid Mermaid diagrams."""
    for p in sorted(SCENARIOS_DIR.glob("P*.json")):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        output = engine.evaluate_scenario(data)
        mermaid = generate_topology_mermaid(output, data)

        assert mermaid.startswith("graph TD"), f"Mermaid output for {p.name} must start with 'graph TD'"
        assert "subgraph Clients" in mermaid or "Infeasible" in mermaid
        assert "subgraph Edge" in mermaid or "Infeasible" in mermaid


def test_topology_svg_structure():
    """Verifies that generated SVG diagrams contain valid XML elements and dark-mode styling."""
    p2_path = SCENARIOS_DIR / "P2.json"
    with open(p2_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = engine.evaluate_scenario(data)
    svg = generate_topology_svg(output, data)

    assert svg.startswith("<svg"), "SVG must start with root <svg>"
    assert "</svg>" in svg, "SVG must have closing </svg>"
    assert 'viewBox="0 0 800' in svg, "SVG must define viewBox"
    assert "<defs>" in svg, "SVG must contain <defs> for arrow markers"
    assert "<marker" in svg, "SVG must contain <marker> element"
    assert "<rect" in svg, "SVG must contain <rect> elements"
    assert "<text" in svg, "SVG must contain <text> elements"
    assert "#090d16" in svg, "SVG must apply dark-mode canvas background"
