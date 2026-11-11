"""Typed domain models for the mandatory input schema (Section 3.1)."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

from stacksense.models.enums import (
    AuthRequirement,
    CloudPreference,
    ComplianceStandard,
    DataResidency,
    DeploymentModel,
    MLRequirement,
    Platform,
    ProjectType,
    TeamExperience,
    TrafficPattern,
    WorkloadType,
)


class ProjectInput(BaseModel):
    name: Optional[str] = Field(default=None, description="Project name")
    type: ProjectType = Field(..., description="Project workload archetype")
    description: Optional[str] = Field(default=None, description="Free text description")
    platforms: list[Platform] = Field(..., min_length=1, description="Target deployment platforms")

    @field_validator("platforms")
    @classmethod
    def validate_platforms_non_empty(cls, v: list[Platform]) -> list[Platform]:
        if not v:
            raise ValueError("platforms list must contain at least one platform")
        return v


class ScaleInput(BaseModel):
    users_at_launch: int = Field(..., ge=0, description="Registered or active users at launch")
    users_12_months: int = Field(..., ge=0, description="Expected users after 12 months")
    peak_concurrent_users: Optional[int] = Field(default=None, ge=0, description="Simultaneous users at peak")
    traffic_pattern: TrafficPattern = Field(default=TrafficPattern.STEADY, description="Traffic burstiness")
    workload: WorkloadType = Field(default=WorkloadType.BALANCED, description="Workload profile")
    data_volume_gb_12_months: Optional[float] = Field(default=None, ge=0.0, description="Total stored data after 12 months in GB")


class TeamInput(BaseModel):
    size: int = Field(..., ge=1, description="Number of engineers")
    experience: TeamExperience = Field(..., description="Team skill level")
    languages: list[str] = Field(default_factory=list, description="Lower-case programming languages")
    has_devops: bool = Field(default=False, description="Whether someone can operate infrastructure")

    @field_validator("languages")
    @classmethod
    def normalize_languages(cls, v: list[str]) -> list[str]:
        return [lang.strip().lower() for lang in v if lang.strip()]


class BudgetInput(BaseModel):
    monthly_infra_usd: float = Field(..., ge=0.0, description="Monthly infrastructure budget in USD")


class TimelineInput(BaseModel):
    mvp_weeks: int = Field(..., ge=1, description="Weeks until the first usable release")


class InfrastructureInput(BaseModel):
    cloud_preference: CloudPreference = Field(default=CloudPreference.ANY, description="Preferred cloud vendor")
    deployment_model: DeploymentModel = Field(default=DeploymentModel.MANAGED_CLOUD, description="Deployment target")
    data_residency: DataResidency = Field(default=DataResidency.NONE, description="Mandatory data residency")
    existing_systems: list[str] = Field(default_factory=list, description="Existing systems to integrate with")


class RequirementsInput(BaseModel):
    realtime: bool = Field(default=False, description="Live updates, chat, collaboration")
    offline_support: bool = Field(default=False, description="Work without connectivity")
    full_text_search: bool = Field(default=False, description="Search over text content")
    file_media_storage: bool = Field(default=False, description="User file/media uploads")
    payments: bool = Field(default=False, description="Takes payments from users")
    auth: AuthRequirement = Field(default=AuthRequirement.NONE, description="Authentication method")
    multi_tenant: bool = Field(default=False, description="Shared multi-tenant system")
    ml_features: MLRequirement = Field(default=MLRequirement.NONE, description="Machine learning features")
    seo_critical: bool = Field(default=False, description="Public pages must rank in search engines")
    availability: str = Field(default="99.9", description="Target availability percentage")
    p95_latency_ms: Optional[int] = Field(default=None, description="Target 95th-percentile latency in ms")

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: str) -> str:
        valid = {"99", "99.9", "99.95", "99.99"}
        if v not in valid:
            raise ValueError(f"availability must be one of {sorted(valid)}")
        return v

    @field_validator("p95_latency_ms")
    @classmethod
    def validate_latency(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("p95_latency_ms must be greater than 0")
        return v


class PrioritiesInput(BaseModel):
    cost: int = Field(default=3, ge=1, le=5)
    time_to_market: int = Field(default=3, ge=1, le=5)
    scalability: int = Field(default=3, ge=1, le=5)
    performance: int = Field(default=3, ge=1, le=5)
    maintainability: int = Field(default=3, ge=1, le=5)
    security: int = Field(default=3, ge=1, le=5)


class ScenarioInput(BaseModel):
    scenario_id: Optional[str] = Field(default=None, description="Scenario ID (e.g. P1, P2)")
    project: ProjectInput
    scale: ScaleInput
    team: TeamInput
    budget: BudgetInput
    timeline: TimelineInput
    infrastructure: InfrastructureInput = Field(default_factory=InfrastructureInput)
    requirements: RequirementsInput = Field(default_factory=RequirementsInput)
    compliance: list[ComplianceStandard] = Field(default_factory=list)
    priorities: PrioritiesInput = Field(default_factory=PrioritiesInput)
    extra_parameters: dict[str, Any] = Field(default_factory=dict, description="Additional custom inputs")

    model_config = {
        "extra": "ignore"
    }
