"""Test deterministic repeatability across runs (FR9 & Section 5.1)."""

import json
from pathlib import Path
import pytest

from stacksense.engine import RecommendationEngine

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "data" / "scenarios"


@pytest.fixture
def engine() -> RecommendationEngine:
    return RecommendationEngine()


@pytest.mark.parametrize("scenario_id", ["P1", "P2", "P3", "P4", "P5", "P6"])
def test_deterministic_output(engine: RecommendationEngine, scenario_id: str):
    file_path = SCENARIOS_DIR / f"{scenario_id}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Run twice
    run1 = engine.evaluate_scenario(data, enable_llm=False).model_dump(exclude_none=True)
    run2 = engine.evaluate_scenario(data, enable_llm=False).model_dump(exclude_none=True)

    # Must be 100% byte-for-byte identical
    assert json.dumps(run1, sort_keys=True) == json.dumps(run2, sort_keys=True)
