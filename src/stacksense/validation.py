"""Input validation and contradiction detection engine for StackSense (FR7 & Section 6)."""

from typing import Any, Tuple

from pydantic import ValidationError

from stacksense.models.enums import (
    ComplianceStandard,
    DeploymentModel,
    EngineStatus,
    Platform,
    TeamExperience,
    WarningSeverity,
)
from stacksense.models.input import ScenarioInput
from stacksense.models.output import ValidationErrorItem, WarningItem

# Curated registry of known deprecated / EOL technologies (Section 6)
DEPRECATED_TECHNOLOGIES: dict[str, str] = {
    "angularjs": "AngularJS (1.x) reached end-of-life on January 1, 2022 and no longer receives security updates.",
    "angular 1": "AngularJS (1.x) reached end-of-life on January 1, 2022 and no longer receives security updates.",
    "python 2": "Python 2.7 reached official end-of-life on January 1, 2020.",
    "python 2.7": "Python 2.7 reached official end-of-life on January 1, 2020.",
    "php 5": "PHP 5.x reached end-of-life in December 2018 and has critical unpatched security vulnerabilities.",
    "php 7": "PHP 7.x reached end-of-life in December 2022.",
    "centos 7": "CentOS 7 reached end-of-life on June 30, 2024.",
    "centos 8": "CentOS 8 reached end-of-life on December 31, 2021.",
    "sql server 2008": "Microsoft SQL Server 2008 / 2008 R2 reached end-of-life in July 2019.",
    "sql server 2012": "Microsoft SQL Server 2012 reached end-of-life in July 2022.",
    "heroku free": "Heroku discontinued free product tiers in November 2022.",
    "ec2-classic": "Amazon EC2-Classic was completely retired in August 2022.",
    "internet explorer": "Internet Explorer 11 reached official end-of-life in June 2022.",
}


def validate_raw_input(raw_data: dict[str, Any]) -> Tuple[ScenarioInput | None, list[ValidationErrorItem], list[str]]:
    """Validates raw dictionary input against Section 3.1 schema.
    
    Returns:
        (ScenarioInput or None, validation_errors, assumptions)
    """
    assumptions: list[str] = []
    
    # Track which optional fields were defaulted
    if "scale" in raw_data and isinstance(raw_data["scale"], dict):
        scale = raw_data["scale"]
        if "traffic_pattern" not in scale:
            assumptions.append("scale.traffic_pattern defaulted to 'steady'")
        if "workload" not in scale:
            assumptions.append("scale.workload defaulted to 'balanced'")
        if "data_volume_gb_12_months" not in scale:
            assumptions.append("scale.data_volume_gb_12_months defaulted to 10 GB")

    if "team" in raw_data and isinstance(raw_data["team"], dict):
        team = raw_data["team"]
        if "has_devops" not in team:
            assumptions.append("team.has_devops defaulted to false")

    if "infrastructure" in raw_data and isinstance(raw_data["infrastructure"], dict):
        infra = raw_data["infrastructure"]
        if "cloud_preference" not in infra:
            assumptions.append("infrastructure.cloud_preference defaulted to 'any'")
        if "deployment_model" not in infra:
            assumptions.append("infrastructure.deployment_model defaulted to 'managed_cloud'")
        if "data_residency" not in infra:
            assumptions.append("infrastructure.data_residency defaulted to 'none'")
        if "existing_systems" not in infra:
            assumptions.append("infrastructure.existing_systems defaulted to empty list")

    if "requirements" in raw_data and isinstance(raw_data["requirements"], dict):
        reqs = raw_data["requirements"]
        for b_field in ["realtime", "offline_support", "full_text_search", "file_media_storage", "payments", "multi_tenant", "seo_critical"]:
            if b_field not in reqs:
                assumptions.append(f"requirements.{b_field} defaulted to false")
        if "auth" not in reqs:
            assumptions.append("requirements.auth defaulted to 'none'")
        if "ml_features" not in reqs:
            assumptions.append("requirements.ml_features defaulted to 'none'")
        if "availability" not in reqs:
            assumptions.append("requirements.availability defaulted to '99.9'")
        if "p95_latency_ms" not in reqs:
            assumptions.append("requirements.p95_latency_ms defaulted to null")

    if "priorities" not in raw_data or not raw_data["priorities"]:
        assumptions.append("All priorities defaulted to 3 (balanced)")

    try:
        scenario = ScenarioInput.model_validate(raw_data)
        return scenario, [], assumptions
    except ValidationError as err:
        errors: list[ValidationErrorItem] = []
        for e in err.errors():
            loc_parts = [str(p) for p in e.get("loc", [])]
            field_name = ".".join(loc_parts)
            msg = e.get("msg", "Validation error")
            errors.append(ValidationErrorItem(field=field_name, message=msg))
        return None, errors, assumptions
    except Exception as exc:
        return None, [ValidationErrorItem(field="root", message=str(exc))], assumptions


def detect_contradictions(scenario: ScenarioInput) -> list[WarningItem]:
    """Detects impossible, conflicting, high-risk, or deprecated requirements per Section 6."""
    warnings: list[WarningItem] = []

    # 1. High scale with zero budget
    if (scenario.scale.users_at_launch > 10000 or scenario.scale.users_12_months > 50000) and scenario.budget.monthly_infra_usd == 0:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_HIGH_SCALE_ZERO_BUDGET",
                severity=WarningSeverity.CRITICAL,
                message=(
                    "High user scale (>10,000 launch or >50,000 12-month users) cannot be sustained on a $0 monthly budget without severe service degradation. "
                    "Relaxation suggestion: Allocate a minimum infrastructure budget of $50-$100/mo for serverless/managed compute, or constrain initial launch users to <1,000."
                ),
                fields=["scale.users_at_launch", "scale.users_12_months", "budget.monthly_infra_usd"],
            )
        )

    # 2. Enterprise 99.99% availability with solo beginner team
    if scenario.requirements.availability == "99.99" and scenario.team.size == 1 and scenario.team.experience == TeamExperience.BEGINNER:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_AVAILABILITY_SOLO_BEGINNER",
                severity=WarningSeverity.CRITICAL,
                message=(
                    "99.99% availability (less than 53 minutes of downtime per year) requires 24/7 on-call rotations, redundant infrastructure, and multi-region failover, which cannot be operated by a single beginner engineer. "
                    "Relaxation suggestion: Lower target availability to 99.5% (standard single-region high availability) or contract managed 24/7 SRE/PaaS support."
                ),
                fields=["requirements.availability", "team.size", "team.experience"],
            )
        )

    # 3. Short timeline with multiple mobile/desktop platforms
    if scenario.timeline.mvp_weeks <= 3 and len(scenario.project.platforms) >= 3 and not scenario.team.has_devops and scenario.team.size <= 2:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_TIGHT_TIMELINE_MANY_PLATFORMS",
                severity=WarningSeverity.WARNING,
                message=(
                    f"Targeting {len(scenario.project.platforms)} platforms ({', '.join(p.value for p in scenario.project.platforms)}) within a {scenario.timeline.mvp_weeks}-week timeline with a {scenario.team.size}-person team creates extreme delivery risk. "
                    "Relaxation suggestion: Focus initial MVP strictly on Web or adopt cross-platform React Native/Flutter to ship from a single codebase."
                ),
                fields=["timeline.mvp_weeks", "project.platforms", "team.size"],
            )
        )

    # 4. Air-gapped / on-premise with managed cloud preference
    if scenario.infrastructure.deployment_model in {DeploymentModel.AIR_GAPPED, DeploymentModel.ON_PREMISE} and scenario.infrastructure.cloud_preference.value in {"aws", "gcp", "azure"}:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_ON_PREM_CLOUD_PREFERENCE",
                severity=WarningSeverity.CRITICAL,
                message=(
                    f"Deployment model '{scenario.infrastructure.deployment_model.value}' is incompatible with managed public cloud preference '{scenario.infrastructure.cloud_preference.value}'. "
                    "Relaxation suggestion: Set cloud_preference to 'none' and deploy on-premise containerized solutions (e.g. MinIO, local PostgreSQL, Docker)."
                ),
                fields=["infrastructure.deployment_model", "infrastructure.cloud_preference"],
            )
        )

    # 5. Offline-first requirement with pure API-only or web-only platform
    if scenario.requirements.offline_support and scenario.project.platforms == [Platform.API_ONLY]:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_OFFLINE_API_ONLY",
                severity=WarningSeverity.CRITICAL,
                message=(
                    "Offline support requested for an api_only platform, but APIs inherently require client-server network connectivity. "
                    "Relaxation suggestion: Include a client application platform (e.g., mobile or desktop with local SQLite caching) or remove the offline_support requirement."
                ),
                fields=["requirements.offline_support", "project.platforms"],
            )
        )

    # 6. Realtime sub-50ms latency with low budget
    if scenario.requirements.p95_latency_ms is not None and scenario.requirements.p95_latency_ms < 50 and scenario.budget.monthly_infra_usd < 100:
        warnings.append(
            WarningItem(
                code="CONTRADICTION_ULTRA_LOW_LATENCY_LOW_BUDGET",
                severity=WarningSeverity.WARNING,
                message=(
                    f"Target latency of {scenario.requirements.p95_latency_ms}ms p95 typically requires dedicated multi-region edge caches or in-memory clusters exceeding the ${scenario.budget.monthly_infra_usd}/month budget. "
                    "Relaxation suggestion: Increase monthly budget to at least $100-$150/mo or relax target p95 latency to 150-200ms."
                ),
                fields=["requirements.p95_latency_ms", "budget.monthly_infra_usd"],
            )
        )

    # 7. Regulatory data residency without supported local cloud
    if scenario.infrastructure.data_residency.value == "india" and scenario.infrastructure.cloud_preference.value == "none" and scenario.infrastructure.deployment_model == DeploymentModel.MANAGED_CLOUD:
        warnings.append(
            WarningItem(
                code="WARNING_DATA_RESIDENCY_UNSPECIFIED_CLOUD",
                severity=WarningSeverity.INFO,
                message="Data residency is set to 'india'; managed cloud deployment must be restricted to cloud regions physically located in India (e.g. AWS ap-south-1, GCP asia-south1, Azure Central India).",
                fields=["infrastructure.data_residency", "infrastructure.deployment_model"],
            )
        )

    # 8. Deprecated Technology Detection in existing_systems (Section 6)
    for sys_item in scenario.infrastructure.existing_systems:
        sys_lower = sys_item.lower()
        for dep_key, dep_msg in DEPRECATED_TECHNOLOGIES.items():
            if dep_key in sys_lower:
                warnings.append(
                    WarningItem(
                        code="DEPRECATED_TECHNOLOGY_DETECTED",
                        severity=WarningSeverity.WARNING,
                        message=f"Existing system '{sys_item}' has reached end-of-life or been retired: {dep_msg} Relaxation suggestion: Target '{sys_item}' for modernization and migrate to supported equivalents rather than extending legacy dependencies.",
                        fields=["infrastructure.existing_systems"],
                    )
                )
                break

    # 9. Skill Mismatch Warning (Section 6)
    has_mobile = any(p in {Platform.ANDROID, Platform.IOS} for p in scenario.project.platforms)
    mobile_langs = {"javascript", "typescript", "dart", "kotlin", "java", "swift"}
    team_langs = set(scenario.team.languages)
    if has_mobile and team_langs and not team_langs.intersection(mobile_langs):
        warnings.append(
            WarningItem(
                code="SKILL_MISMATCH_MOBILE_LANGUAGES",
                severity=WarningSeverity.INFO,
                message=f"Team possesses skills in {', '.join(sorted(team_langs))}, but target platforms include mobile. The engine recommends React Native or Flutter, requiring team onboarding for UI development.",
                fields=["team.languages", "project.platforms"],
            )
        )

    return warnings
