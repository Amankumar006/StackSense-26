"""Comprehensive test suite for Section 6 Edge Cases in the StackSense engine.

Covers all 9 required categories:
1. Missing fields
2. Invalid values
3. Contradictions
4. Over-engineering traps
5. Regulatory constraints
6. Existing systems
7. Restricted deployment
8. Skill mismatch
9. Deprecated technology
"""

import json
from pathlib import Path
import pytest

from stacksense.engine import RecommendationEngine
from stacksense.models.enums import EngineStatus, WarningSeverity

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "edge_cases"


@pytest.fixture
def engine():
    return RecommendationEngine()


def _load_scenario(filename: str) -> dict:
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def test_edge_case_missing_fields(engine):
    """Category 1: Missing fields - defaults applied and listed in assumptions."""
    raw = _load_scenario("E1_missing_optional_fields.json")
    out = engine.evaluate_scenario(raw)

    assert out.status in {EngineStatus.OK, EngineStatus.OK_WITH_WARNINGS}
    assert out.stack is not None
    assert out.stack.frontend.choice == "Astro"
    assert out.stack.backend.choice == "None"
    assert out.stack.database.choice == "None"
    assert out.stack.hosting.choice == "Netlify (Free)"

    # Documented defaults must be recorded in assumptions
    assert len(out.assumptions) >= 5
    assumptions_text = " ".join(out.assumptions)
    assert "traffic_pattern" in assumptions_text
    assert "deployment_model" in assumptions_text


def test_edge_case_invalid_values(engine):
    """Category 2: Invalid values - field-level validation errors, never crash."""
    raw = _load_scenario("E2_invalid_values.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.INVALID_INPUT
    assert out.stack is None
    assert len(out.validation_errors) >= 5

    error_fields = {err.field for err in out.validation_errors}
    assert "project.type" in error_fields
    assert "scale.users_at_launch" in error_fields
    assert "budget.monthly_infra_usd" in error_fields
    assert "priorities.cost" in error_fields


def test_edge_case_contradiction_high_scale_zero_budget(engine):
    """Category 3a: Contradiction - High scale with zero budget."""
    raw = _load_scenario("E3_contradiction_scale_zero_budget.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK_WITH_WARNINGS
    assert out.stack is not None
    warning_codes = {w.code for w in out.warnings}
    assert "CONTRADICTION_HIGH_SCALE_ZERO_BUDGET" in warning_codes

    crit_warnings = [w for w in out.warnings if w.code == "CONTRADICTION_HIGH_SCALE_ZERO_BUDGET"]
    assert crit_warnings[0].severity == WarningSeverity.CRITICAL


def test_edge_case_contradiction_solo_beginner_availability(engine):
    """Category 3b: Contradiction - 99.99% availability with solo beginner."""
    raw = _load_scenario("E4_contradiction_solo_beginner_availability.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK_WITH_WARNINGS
    assert out.stack is not None
    warning_codes = {w.code for w in out.warnings}
    assert "CONTRADICTION_AVAILABILITY_SOLO_BEGINNER" in warning_codes

    crit_warnings = [w for w in out.warnings if w.code == "CONTRADICTION_AVAILABILITY_SOLO_BEGINNER"]
    assert crit_warnings[0].severity == WarningSeverity.CRITICAL


def test_edge_case_contradiction_airgapped_managed_cloud(engine):
    """Category 3c: Contradiction - Air-gapped with public cloud preference (Infeasible)."""
    raw = _load_scenario("E5_contradiction_airgapped_managed_cloud.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.INFEASIBLE
    assert out.stack is None
    warning_codes = {w.code for w in out.warnings}
    assert "CONTRADICTION_ON_PREM_CLOUD_PREFERENCE" in warning_codes


def test_edge_case_overengineering_trap(engine):
    """Category 4: Over-engineering traps - High traffic that is actually static."""
    raw = _load_scenario("E6_overengineering_trap_static.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK
    assert out.stack is not None
    assert out.stack.frontend.choice == "Astro"
    assert out.stack.backend.choice == "None"
    assert out.stack.database.choice == "None"
    assert out.stack.hosting.choice == "Netlify / Edge CDN"

    # Verify that alternatives explicitly reject Kubernetes and Microservices
    hosting_alt_choices = {alt.choice for alt in out.stack.hosting.alternatives}
    assert "Kubernetes Cluster (EKS / GKE)" in hosting_alt_choices

    backend_alt_choices = {alt.choice for alt in out.stack.backend.alternatives}
    assert "Microservices Architecture" in backend_alt_choices


def test_edge_case_regulatory_constraints(engine):
    """Category 5: Regulatory constraints - RBI data localisation, DPDP, PCI-DSS in India."""
    raw = _load_scenario("E7_regulatory_rbi_dpdp_india.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK
    assert out.stack is not None
    assert out.stack.backend.choice == "Spring Boot"
    assert out.stack.database.choice == "Amazon Aurora PostgreSQL"
    assert out.stack.hosting.choice == "AWS ECS Fargate"

    supporting_choices = {s.choice for s in out.stack.supporting}
    assert "Razorpay Payment Gateway" in supporting_choices
    assert "Amazon SQS FIFO" in supporting_choices

    # Compliance must be tracked in driven_by
    assert "compliance" in out.stack.backend.driven_by
    assert "compliance" in out.stack.database.driven_by


def test_edge_case_existing_systems(engine):
    """Category 6: Existing systems - Reuse legacy on-prem SQL Server and Microsoft Entra ID."""
    raw = _load_scenario("E8_existing_systems_microsoft.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK
    assert out.stack is not None
    assert out.stack.backend.choice == "ASP.NET Core (.NET 8)"
    assert out.stack.database.choice == "Microsoft SQL Server"
    assert out.stack.hosting.choice == "Azure App Service"

    supporting_choices = {s.choice for s in out.stack.supporting}
    assert "Microsoft Entra ID (Azure AD)" in supporting_choices
    assert "infrastructure.existing_systems" in out.stack.backend.driven_by
    assert "infrastructure.existing_systems" in out.stack.database.driven_by


def test_edge_case_restricted_deployment(engine):
    """Category 7: Restricted deployment - On-premise / air-gapped strictly eliminates cloud PaaS/CDNs."""
    raw = _load_scenario("E9_restricted_deployment_on_premise.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK
    assert out.stack is not None
    assert out.stack.hosting.choice == "On-Premise Server (Docker Compose / Podman)"
    assert out.stack.database.choice == "PostgreSQL"

    supporting_choices = {s.choice for s in out.stack.supporting}
    assert "MinIO (Self-Hosted S3-Compatible Storage)" in supporting_choices
    assert "Keycloak (Self-Hosted Identity)" in supporting_choices
    assert "RabbitMQ (Self-Hosted)" in supporting_choices

    # Ensure no AWS, GCP, or Azure public SaaS were selected
    all_choices = [
        out.stack.frontend.choice,
        out.stack.backend.choice,
        out.stack.database.choice,
        out.stack.hosting.choice,
        *[s.choice for s in out.stack.supporting],
    ]
    for c in all_choices:
        assert "AWS" not in c
        assert "Amazon S3" not in c
        assert "Google Cloud" not in c
        assert "Azure" not in c


def test_edge_case_skill_mismatch(engine):
    """Category 8: Skill mismatch - Python-only team developing mobile app."""
    raw = _load_scenario("E10_skill_mismatch_python_only.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK
    assert out.stack is not None
    assert out.stack.frontend.choice in {"React Native (Expo)", "Flutter"}
    assert out.stack.backend.choice == "FastAPI"

    warning_codes = {w.code for w in out.warnings}
    assert "SKILL_MISMATCH_MOBILE_LANGUAGES" in warning_codes


def test_edge_case_deprecated_technology(engine):
    """Category 9: Deprecated technology - Never recommend, warn about EOL existing systems."""
    raw = _load_scenario("E11_deprecated_existing_systems.json")
    out = engine.evaluate_scenario(raw)

    assert out.status == EngineStatus.OK_WITH_WARNINGS
    assert out.stack is not None

    dep_warnings = [w for w in out.warnings if w.code == "DEPRECATED_TECHNOLOGY_DETECTED"]
    assert len(dep_warnings) == 3

    warning_text = " ".join(w.message for w in dep_warnings)
    assert "AngularJS" in warning_text
    assert "Python 2.7" in warning_text
    assert "CentOS 7" in warning_text

    # Deprecated technologies must NEVER appear in recommendations
    all_choices = [
        out.stack.frontend.choice,
        out.stack.backend.choice,
        out.stack.database.choice,
        out.stack.hosting.choice,
        *[s.choice for s in out.stack.supporting],
    ]
    for c in all_choices:
        assert "AngularJS" not in c
        assert "Python 2" not in c
        assert "CentOS" not in c
