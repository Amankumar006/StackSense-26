"""Hard-constraint evaluator for StackSense (Section 5.3).

Evaluates non-negotiable boundaries:
- data_residency
- compliance
- deployment_model
- explicit cloud_preference
"""

from typing import Any
from stacksense.models.enums import (
    CloudPreference,
    ComplianceStandard,
    DataResidency,
    DeploymentModel,
)
from stacksense.models.input import ScenarioInput


def is_candidate_compliant(candidate: dict[str, Any], scenario: ScenarioInput) -> tuple[bool, str]:
    """Evaluates whether a single technology candidate satisfies all hard constraints.
    
    Returns:
        (is_valid, rejection_reason)
    """
    infra = scenario.infrastructure

    # 1. Deployment Model Constraint
    cand_models = set(candidate.get("deployment_models", []))
    if infra.deployment_model == DeploymentModel.ON_PREMISE:
        if "on_prem" not in cand_models and "self_hosted" not in cand_models:
            return False, f"Not deployable on-premise (supports: {', '.join(cand_models)})"
    elif infra.deployment_model == DeploymentModel.AIR_GAPPED:
        if "air_gapped" not in cand_models:
            return False, "Not certified for air-gapped offline environments"

    # 2. Cloud Preference Constraint (if explicitly set to aws/gcp/azure)
    if infra.cloud_preference != CloudPreference.ANY and infra.cloud_preference != CloudPreference.NONE:
        cid = candidate.get("id", "").lower()
        if infra.cloud_preference == CloudPreference.AWS:
            if cid.startswith("azure_") or cid.startswith("google_") or cid == "mssql_server":
                return False, f"Incompatible with explicit cloud preference for AWS (candidate is {candidate.get('name')})"
        elif infra.cloud_preference == CloudPreference.GCP:
            if cid.startswith("aws_") or cid.startswith("azure_") or cid == "mssql_server":
                return False, f"Incompatible with explicit cloud preference for GCP (candidate is {candidate.get('name')})"
        elif infra.cloud_preference == CloudPreference.AZURE:
            if cid.startswith("aws_") or cid.startswith("google_"):
                return False, f"Incompatible with explicit cloud preference for Azure (candidate is {candidate.get('name')})"

    # 3. Data Residency Constraint
    if infra.data_residency == DataResidency.INDIA:
        # Check if hosting/database violates India residency
        notes = candidate.get("regions_or_residency_notes", "").lower()
        cid = candidate.get("id", "").lower()
        if candidate.get("category") in {"hosting", "database", "storage"}:
            if "agnostic" not in notes and "india" not in notes and "mumbai" not in notes and "self-hostable" not in notes and "device" not in notes and "n/a" not in notes:
                return False, f"Lacks documented physical data center availability in India (notes: {notes})"

    # 4. Regulatory Localisation (RBI)
    if ComplianceStandard.RBI_LOCALISATION in scenario.compliance:
        if candidate.get("category") in {"database", "storage", "payments"}:
            caps = set(candidate.get("capabilities", []))
            cid = candidate.get("id", "")
            if cid not in {"postgresql", "amazon_aurora_postgres", "aws_s3", "razorpay", "sqlite_embedded"}:
                if "rbi_localisation" not in caps and "rbi_compliant" not in caps:
                    return False, "Not documented as compliant with RBI payment data localization mandates"

    return True, ""


def filter_candidates(candidates: list[dict[str, Any]], scenario: ScenarioInput) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Filters candidate list against hard constraints.
    
    Returns:
        (valid_candidates, rejected_candidates_with_reasons)
    """
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for c in candidates:
        ok, reason = is_candidate_compliant(c, scenario)
        if ok:
            valid.append(c)
        else:
            rejected.append({"choice": c.get("name", c.get("id")), "id": c.get("id"), "why_not": reason})

    return valid, rejected
