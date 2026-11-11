"""Typed domain models for the mandatory output schema (Section 4)."""

from typing import Optional
from pydantic import BaseModel, Field

from stacksense.models.enums import ArchitectureStyle, EngineStatus, WarningSeverity


class AlternativeItem(BaseModel):
    choice: str = Field(..., description="Alternative technology considered")
    why_not: str = Field(..., description="Concrete comparative reason why this alternative was rejected")


class CoreComponent(BaseModel):
    choice: str = Field(..., description="Recommended technology or 'None' if justified")
    justification: str = Field(..., description="Why this fits the project requirements")
    driven_by: list[str] = Field(default_factory=list, description="Input field paths driving this choice")
    alternatives: list[AlternativeItem] = Field(default_factory=list, description="At least one viable alternative")
    tradeoffs: list[str] = Field(default_factory=list, description="Known downsides of the choice")


class SupportingComponent(BaseModel):
    layer: str = Field(..., description="Supporting layer (cache, queue, search, auth, storage, cdn, realtime, payments, ml, ci_cd, observability, other)")
    choice: str = Field(..., description="Recommended technology or service")
    justification: str = Field(..., description="Why this fits the given inputs")
    driven_by: list[str] = Field(default_factory=list, description="Input field paths driving this supporting service")
    alternatives: list[AlternativeItem] = Field(default_factory=list, description="Viable alternatives considered")
    tradeoffs: list[str] = Field(default_factory=list, description="Known downsides of the choice")


class StackRecommendation(BaseModel):
    frontend: CoreComponent
    backend: CoreComponent
    database: CoreComponent
    hosting: CoreComponent
    supporting: list[SupportingComponent] = Field(default_factory=list)


class EstimatedMonthlyCost(BaseModel):
    min: float = Field(..., ge=0.0, description="Minimum estimated monthly cost in USD")
    max: float = Field(..., ge=0.0, description="Maximum estimated monthly cost in USD")
    assumptions: list[str] = Field(default_factory=list, description="Cost basis and usage assumptions")


class WarningItem(BaseModel):
    code: str = Field(..., description="Warning identifier code (e.g. FREE_TIER_LIMITS, SOFT_CONSTRAINT_RELAXED)")
    severity: WarningSeverity = Field(..., description="info, warning, or critical")
    message: str = Field(..., description="Plain language explanation of risk or conflict")
    fields: list[str] = Field(default_factory=list, description="Input field paths associated with this warning")


class ValidationErrorItem(BaseModel):
    field: str = Field(..., description="Input field path with an error")
    message: str = Field(..., description="Validation failure explanation")


class ScenarioOutput(BaseModel):
    scenario_id: Optional[str] = Field(default=None, description="Scenario ID (e.g. P1, P2)")
    engine_version: str = Field(default="1.0.0", description="StackSense engine version")
    status: EngineStatus = Field(..., description="'ok', 'ok_with_warnings', 'infeasible', or 'invalid_input'")
    summary: str = Field(..., description="One or two sentences describing the recommended approach")
    architecture_style: Optional[ArchitectureStyle] = Field(default=None, description="static, monolith, modular_monolith, serverless, microservices, hybrid, other")
    stack: Optional[StackRecommendation] = Field(default=None, description="Complete recommended stack (null if invalid_input)")
    estimated_monthly_cost_usd: Optional[EstimatedMonthlyCost] = Field(default=None, description="Order of magnitude cost band")
    warnings: list[WarningItem] = Field(default_factory=list, description="Warnings and conflict notices")
    assumptions: list[str] = Field(default_factory=list, description="Defaults or interpretations applied")
    validation_errors: list[ValidationErrorItem] = Field(default_factory=list, description="Field errors if invalid_input")
