"""Unit tests for input validation and contradiction detection (FR7 & Section 6)."""

import pytest

from stacksense.engine import RecommendationEngine
from stacksense.models.enums import EngineStatus
from stacksense.validation import detect_contradictions, validate_raw_input


@pytest.fixture
def engine() -> RecommendationEngine:
    return RecommendationEngine()


def test_missing_required_fields(engine: RecommendationEngine):
    """Missing required fields must yield invalid_input and stack=null."""
    raw = {
        "project": {"name": "Incomplete"},
        "scale": {"users_at_launch": 100},
    }
    result = engine.evaluate_scenario(raw)
    assert result.status == EngineStatus.INVALID_INPUT
    assert result.stack is None
    assert len(result.validation_errors) > 0


def test_invalid_ranges_and_negatives(engine: RecommendationEngine):
    """Negative scale or budget values must be caught as field-level errors."""
    raw = {
        "project": {"type": "web_app", "platforms": ["web"]},
        "scale": {"users_at_launch": -10, "users_12_months": -50},
        "team": {"size": 0, "experience": "beginner", "languages": []},
        "budget": {"monthly_infra_usd": -100},
        "timeline": {"mvp_weeks": 0},
    }
    result = engine.evaluate_scenario(raw)
    assert result.status == EngineStatus.INVALID_INPUT
    assert result.stack is None
    error_fields = {e.field for e in result.validation_errors}
    assert "scale.users_at_launch" in error_fields
    assert "team.size" in error_fields
    assert "budget.monthly_infra_usd" in error_fields
    assert "timeline.mvp_weeks" in error_fields


def test_infeasible_contradiction(engine: RecommendationEngine):
    """Air-gapped deployment with AWS cloud preference must yield infeasible status."""
    raw = {
        "scenario_id": "EDGE_ONPREM_AWS",
        "project": {"type": "internal_tool", "platforms": ["web"]},
        "scale": {"users_at_launch": 100, "users_12_months": 500},
        "team": {"size": 2, "experience": "intermediate", "languages": ["python"]},
        "budget": {"monthly_infra_usd": 200},
        "timeline": {"mvp_weeks": 8},
        "infrastructure": {
            "deployment_model": "air_gapped",
            "cloud_preference": "aws",
        },
    }
    result = engine.evaluate_scenario(raw)
    assert result.status == EngineStatus.INFEASIBLE
    assert result.stack is None
    assert any(w.code == "CONTRADICTION_ON_PREM_CLOUD_PREFERENCE" for w in result.warnings)
