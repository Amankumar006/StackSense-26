"""Integration tests for all 6 public benchmark scenarios (P1 through P6)."""

import json
from pathlib import Path
import pytest

from stacksense.engine import RecommendationEngine
from stacksense.models.enums import EngineStatus

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "data" / "scenarios"


@pytest.fixture
def engine() -> RecommendationEngine:
    return RecommendationEngine()


@pytest.mark.parametrize("scenario_id", ["P1", "P2", "P3", "P4", "P5", "P6"])
def test_public_scenario_execution(engine: RecommendationEngine, scenario_id: str):
    file_path = SCENARIOS_DIR / f"{scenario_id}.json"
    assert file_path.exists(), f"Scenario fixture not found: {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = engine.evaluate_scenario(data, enable_llm=False)

    # 1. Status must be ok or ok_with_warnings
    assert result.status in {EngineStatus.OK, EngineStatus.OK_WITH_WARNINGS}
    assert result.validation_errors == []

    # 2. Stack must be present
    assert result.stack is not None
    stack = result.stack

    # 3. Each core layer must have choice, justification, driven_by, and >= 1 alternative with why_not
    for layer_name in ["frontend", "backend", "database", "hosting"]:
        component = getattr(stack, layer_name)
        assert component.choice, f"{layer_name} choice must not be empty"
        assert component.justification, f"{layer_name} justification must not be empty"
        assert len(component.driven_by) >= 1, f"{layer_name} must have at least one driven_by field"
        assert len(component.alternatives) >= 1, f"{layer_name} must have at least one alternative"
        for alt in component.alternatives:
            assert alt.choice, "Alternative choice must not be empty"
            assert alt.why_not, "Alternative why_not must not be empty"

    # 4. Cost band must be non-negative and min <= max
    assert result.estimated_monthly_cost_usd is not None
    cost = result.estimated_monthly_cost_usd
    assert cost.min >= 0
    assert cost.max >= cost.min
    assert len(cost.assumptions) >= 1

    # 5. Summary must be populated
    assert len(result.summary) > 20
