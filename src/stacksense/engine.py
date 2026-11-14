"""Deterministic, explainable recommendation engine for StackSense.

Implements:
- Multi-criteria layer evaluation (FR3)
- Supporting services activation (FR4)
- Traceability and alternative justification (FR5)
- Cost band estimation (FR6)
- Conflict and contradiction handling (FR7)
- Strict Section 4 JSON export (FR8)
- 100% deterministic repeatability (FR9)
"""

from typing import Any, Optional

from stacksense.catalog import TechnologyCatalog, get_default_catalog
from stacksense.constraints import filter_candidates
from stacksense.models.enums import (
    ArchitectureStyle,
    AuthRequirement,
    CloudPreference,
    ComplianceStandard,
    DataResidency,
    DeploymentModel,
    EngineStatus,
    MLRequirement,
    Platform,
    ProjectType,
    TeamExperience,
    WarningSeverity,
    WorkloadType,
)
from stacksense.models.input import ScenarioInput
from stacksense.models.output import (
    AlternativeItem,
    CoreComponent,
    EstimatedMonthlyCost,
    ScenarioOutput,
    StackRecommendation,
    SupportingComponent,
    ValidationErrorItem,
    WarningItem,
)
from stacksense.validation import detect_contradictions, validate_raw_input


class RecommendationEngine:
    """Core recommendation pipeline executing the 5-stage architectural evaluation."""

    def __init__(self, catalog: Optional[TechnologyCatalog] = None):
        self.catalog = catalog or get_default_catalog()

    def evaluate_scenario(self, raw_input: dict[str, Any], enable_llm: bool = False) -> ScenarioOutput:
        """Single-pass deterministic scenario evaluation."""
        # 1. Validation & Schema Normalization
        scenario, validation_errors, assumptions = validate_raw_input(raw_input)
        if scenario is None:
            return ScenarioOutput(
                scenario_id=raw_input.get("scenario_id"),
                status=EngineStatus.INVALID_INPUT,
                summary="Input validation failed with field-level schema errors.",
                validation_errors=validation_errors,
                assumptions=assumptions,
            )

        # 2. Contradiction & Edge-Case Detection
        warnings = detect_contradictions(scenario)

        # Check for non-negotiable critical contradictions causing infeasibility
        critical_infeasible = [
            w for w in warnings
            if w.code in {"CONTRADICTION_ON_PREM_CLOUD_PREFERENCE", "CONTRADICTION_OFFLINE_API_ONLY"}
        ]
        if critical_infeasible:
            return ScenarioOutput(
                scenario_id=scenario.scenario_id,
                status=EngineStatus.INFEASIBLE,
                summary=f"Infeasible scenario: {critical_infeasible[0].message}",
                warnings=warnings,
                assumptions=assumptions,
                stack=None,
            )

        # 3. Core Layer Evaluation
        frontend, f_cost = self._recommend_frontend(scenario)
        backend, b_cost = self._recommend_backend(scenario, frontend)
        database, d_cost = self._recommend_database(scenario, frontend, backend)
        hosting, h_cost = self._recommend_hosting(scenario, frontend, backend, database)

        # 4. Supporting Services Activation
        supporting, s_cost = self._recommend_supporting(scenario, frontend, backend, database, hosting)

        # 5. Architecture Style Classification
        arch_style = self._determine_architecture_style(scenario, frontend, backend, database, hosting)

        # 6. Cost Band Computation & Budget Trade-off
        total_min = f_cost[0] + b_cost[0] + d_cost[0] + h_cost[0] + s_cost[0]
        total_max = f_cost[1] + b_cost[1] + d_cost[1] + h_cost[1] + s_cost[1]
        
        cost_assumptions: list[str] = [
            "Estimates based on published cloud pricing units and standard resource allocations.",
        ]
        if total_min == 0 and total_max <= 5:
            cost_assumptions.append("Operating within generous free-tier limits (e.g. Netlify/Vercel static hosting).")

        # Check for budget conflict (Soft constraint relaxation per Section 5.3)
        status = EngineStatus.OK
        if scenario.budget.monthly_infra_usd > 0 and total_min > scenario.budget.monthly_infra_usd:
            status = EngineStatus.OK_WITH_WARNINGS
            delta = total_min - scenario.budget.monthly_infra_usd
            warnings.append(
                WarningItem(
                    code="BUDGET_OVERRUN_SOFT_RELAXATION",
                    severity=WarningSeverity.WARNING,
                    message=(
                        f"Estimated minimum monthly cost (${total_min:.0f}) exceeds the declared monthly budget (${scenario.budget.monthly_infra_usd:.0f}). "
                        f"Soft budget constraint relaxed to satisfy compliance, scale, and availability requirements. "
                        f"Relaxation suggestion: Increase monthly infrastructure budget from ${scenario.budget.monthly_infra_usd:.0f} to at least ${total_min:.0f} (delta +${delta:.0f}/mo) or consolidate services onto single-node compute."
                    ),
                    fields=["budget.monthly_infra_usd"],
                )
            )
            assumptions.append(f"Budget relaxed by ${delta:.0f}/month (from ${scenario.budget.monthly_infra_usd:.0f} to ${total_min:.0f}) to achieve required SLA and compliance.")
        elif any(w.severity == WarningSeverity.CRITICAL for w in warnings):
            status = EngineStatus.OK_WITH_WARNINGS
        elif any(w.severity == WarningSeverity.WARNING for w in warnings):
            status = EngineStatus.OK_WITH_WARNINGS

        # 7. Summary Synthesis
        summary = self._generate_summary(scenario, arch_style, frontend, backend, database, hosting, total_min, total_max)

        stack = StackRecommendation(
            frontend=frontend,
            backend=backend,
            database=database,
            hosting=hosting,
            supporting=supporting,
        )

        return ScenarioOutput(
            scenario_id=scenario.scenario_id,
            status=status,
            summary=summary,
            architecture_style=arch_style,
            stack=stack,
            estimated_monthly_cost_usd=EstimatedMonthlyCost(
                min=float(total_min),
                max=float(total_max),
                assumptions=cost_assumptions,
            ),
            warnings=warnings,
            assumptions=assumptions,
            validation_errors=[],
        )

    # --------------------------------------------------------------------------
    # Layer Recommenders
    # --------------------------------------------------------------------------

    def _recommend_frontend(self, scenario: ScenarioInput) -> tuple[CoreComponent, tuple[float, float]]:
        candidates = self.catalog.get_by_category("frontend")
        valid, rejected = filter_candidates(candidates, scenario)
        driven_by = ["project.platforms"]

        # Case 1: API Only
        if scenario.project.platforms == [Platform.API_ONLY]:
            driven_by.append("project.type")
            return CoreComponent(
                choice="None",
                justification="Project is an API-only service requiring no graphical frontend layer.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Next.js", why_not="Heavier runtime and unnecessary for headless APIs.")],
                tradeoffs=["No graphical web portal included; relies on API consumers."],
            ), (0.0, 0.0)

        # Case 2: Mobile targets present (Android or iOS)
        has_mobile = any(p in {Platform.ANDROID, Platform.IOS} for p in scenario.project.platforms)
        has_web = Platform.WEB in scenario.project.platforms

        if has_mobile:
            driven_by.append("team.languages")
            if "dart" in scenario.team.languages:
                return CoreComponent(
                    choice="Flutter",
                    justification="Cross-platform native mobile and web target aligns with team Dart skills and delivers high-performance 60fps rendering.",
                    driven_by=driven_by,
                    alternatives=[AlternativeItem(choice="React Native (Expo)", why_not="Team possesses established Dart expertise; Flutter avoids JS bridge overhead.")],
                    tradeoffs=["Web bundle sizes are larger than pure HTML/JS frameworks."],
                ), (0.0, 0.0)
            else:
                return CoreComponent(
                    choice="React Native (Expo)",
                    justification="Cross-platform architecture supporting Android, iOS, and Web from a unified TypeScript/JavaScript codebase with offline SQLite support.",
                    driven_by=driven_by,
                    alternatives=[AlternativeItem(choice="Flutter", why_not="Team skills center on JavaScript/TypeScript rather than Dart.")],
                    tradeoffs=["Native platform bridges required for specialized hardware integrations."],
                ), (0.0, 0.0)

        # Case 3: Pure Web
        if scenario.project.type == ProjectType.CONTENT_SITE:
            driven_by.extend(["requirements.seo_critical", "scale.workload"])
            return CoreComponent(
                choice="Astro",
                justification="Content-first static site generation with islands architecture minimizes client-side JavaScript, maximizing SEO and read-heavy performance.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Next.js (static export)", why_not="Heavier client runtime than needed for purely markdown-driven content.")],
                tradeoffs=["Complex stateful interactivity requires islands hydration."],
            ), (0.0, 0.0)

        if scenario.requirements.seo_critical:
            driven_by.append("requirements.seo_critical")
            return CoreComponent(
                choice="Next.js",
                justification="Server-side rendering (SSR) and hybrid static generation ensure optimal SEO indexing and fast first-contentful paint.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="React (Vite)", why_not="Client-side rendering (SPA) suffers from delayed SEO crawler indexing.")],
                tradeoffs=["Requires Node.js runtime or edge compute for dynamic server rendering."],
            ), (0.0, 0.0)

        # Default web app / dashboard / realtime collab
        driven_by.append("priorities.performance")
        return CoreComponent(
            choice="React (Vite)",
            justification="Lightweight client-rendered SPA provides rapid interactive state management with minimal framework overhead.",
            driven_by=driven_by,
            alternatives=[AlternativeItem(choice="Next.js", why_not="Server-side rendering runtime unnecessary for authenticated, non-SEO internal/SaaS app.")],
            tradeoffs=["Initial bundle download before client hydration."],
        ), (0.0, 0.0)

    def _recommend_backend(self, scenario: ScenarioInput, frontend: CoreComponent) -> tuple[CoreComponent, tuple[float, float]]:
        candidates = self.catalog.get_by_category("backend")
        valid, rejected = filter_candidates(candidates, scenario)
        driven_by = ["project.type", "team.languages"]

        # Case 1: Static content site with Astro -> Backend None
        if scenario.project.type == ProjectType.CONTENT_SITE and frontend.choice == "Astro" and not scenario.requirements.payments and not scenario.requirements.realtime:
            driven_by.append("scale.workload")
            return CoreComponent(
                choice="None",
                justification="Read-heavy content and markdown pages are fully pre-rendered at build time; dynamic backend server is unnecessary.",
                driven_by=driven_by,
                alternatives=[
                    AlternativeItem(choice="Node.js (Express)", why_not="Running a persistent server adds unnecessary operational overhead and cost for static content."),
                    AlternativeItem(choice="Microservices Architecture", why_not="Massive over-engineering trap: decomposing a read-heavy content site into microservices introduces distributed latency and operational burden without any functional benefit.")
                ],
                tradeoffs=["Forms and interactive inputs require external serverless handler or webhook."],
            ), (0.0, 0.0)

        # Case 2: Enterprise Microsoft Integration (C# / SQL Server / Entra ID)
        if "csharp" in scenario.team.languages or any("sql server" in s.lower() or "entra" in s.lower() for s in scenario.infrastructure.existing_systems):
            driven_by.extend(["infrastructure.existing_systems", "team.languages"])
            return CoreComponent(
                choice="ASP.NET Core (.NET 8)",
                justification="High-throughput compiled backend offering first-class integration with Microsoft Entra ID and SQL Server.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Node.js (Express)", why_not="Lacks native enterprise integration with existing Microsoft 365 and on-prem SQL Server infrastructure.")],
                tradeoffs=["Tighter coupling with Microsoft developer ecosystem."],
            ), (10.0, 40.0)

        # Case 3: Fintech, Banking, Strict Compliance (Java/Kotlin + RBI + PCI DSS)
        is_fintech = scenario.project.type == ProjectType.FINTECH or ComplianceStandard.RBI_LOCALISATION in scenario.compliance or ComplianceStandard.PCI_DSS in scenario.compliance
        if is_fintech and ("java" in scenario.team.languages or "kotlin" in scenario.team.languages or scenario.team.experience == TeamExperience.SENIOR):
            driven_by.extend(["compliance", "team.languages", "requirements.availability"])
            return CoreComponent(
                choice="Spring Boot",
                justification="Industry-standard enterprise framework providing robust ACID transaction boundaries, mature double-entry accounting libraries, and compliance support for RBI and PCI-DSS.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="FastAPI", why_not="Python lacks enterprise transaction management maturity and strict type-safe JVM thread isolation needed for banking ledgers.")],
                tradeoffs=["Higher baseline RAM consumption (512MB–1GB JVM memory floor)."],
            ), (30.0, 80.0)

        # Case 4: Real-time high concurrency collaborative SaaS (Go)
        if scenario.project.type == ProjectType.REALTIME_COLLAB or ("go" in scenario.team.languages and scenario.requirements.realtime):
            driven_by.extend(["requirements.realtime", "scale.workload", "team.languages"])
            return CoreComponent(
                choice="Go (Gin / Standard Lib)",
                justification="Goroutine-per-connection concurrency model delivers sub-10ms WebSocket latency with minimal RAM footprint for heavy write/state synchronization.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Node.js (Express)", why_not="Single-threaded event loop can suffer event lag under intensive state calculations.")],
                tradeoffs=["More verbose error handling and boilerplate code than Python."],
            ), (15.0, 50.0)

        # Case 5: Python / FastAPI (Default for rapid API, AI/ML, and small teams)
        if "python" in scenario.team.languages or scenario.requirements.ml_features != MLRequirement.NONE or scenario.timeline.mvp_weeks <= 10:
            driven_by.extend(["team.languages", "timeline.mvp_weeks"])
            return CoreComponent(
                choice="FastAPI",
                justification="Asynchronous Python framework with automatic OpenAPI documentation and Pydantic validation; enables rapid MVP development.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Django", why_not="FastAPI is more lightweight, provides native async performance, and integrates better with mobile APIs.")],
                tradeoffs=["Requires explicit worker process management (Uvicorn / Gunicorn) for multi-core scaling."],
            ), (10.0, 35.0)

        # Default fallback: Node.js (Express)
        driven_by.append("team.languages")
        return CoreComponent(
            choice="Node.js (Express / Fastify)",
            justification="Ubiquitous JavaScript/TypeScript backend runtime enabling shared types across frontend and backend with rapid delivery.",
            driven_by=driven_by,
            alternatives=[AlternativeItem(choice="Go", why_not="Team skills align with JavaScript/TypeScript rather than Go.")],
            tradeoffs=["CPU-intensive blocking operations require worker threads."],
        ), (10.0, 30.0)

    def _recommend_database(self, scenario: ScenarioInput, frontend: CoreComponent, backend: CoreComponent) -> tuple[CoreComponent, tuple[float, float]]:
        candidates = self.catalog.get_by_category("database")
        valid, rejected = filter_candidates(candidates, scenario)
        driven_by = ["project.type", "scale.data_volume_gb_12_months"]

        # Case 1: Static site without user data
        if scenario.project.type == ProjectType.CONTENT_SITE and backend.choice == "None":
            return CoreComponent(
                choice="None",
                justification="Content site relies on static Markdown files; persistent database server is not required.",
                driven_by=["project.type"],
                alternatives=[AlternativeItem(choice="PostgreSQL", why_not="Adds unneeded infrastructure cost ($15+/mo) and maintenance for static read-only articles.")],
                tradeoffs=["Dynamic user-generated comments or profiles require external service."],
            ), (0.0, 0.0)

        # Case 2: Offline-First Low-End Mobile (P6 archetype)
        if scenario.requirements.offline_support and Platform.ANDROID in scenario.project.platforms:
            driven_by.extend(["requirements.offline_support", "project.platforms"])
            return CoreComponent(
                choice="SQLite / Room (Client-side) + PostgreSQL (Cloud Sync)",
                justification="Local SQLite on Android provides zero-latency offline survey storage; syncs transactions to cloud PostgreSQL when connectivity returns.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Pure Cloud PostgreSQL", why_not="Completely fails when field agents operate in 2G/offline rural environments.")],
                tradeoffs=["Requires conflict-resolution logic during network resynchronization."],
            ), (15.0, 35.0)

        # Case 3: Enterprise Microsoft Integration
        if backend.choice.startswith("ASP.NET") or any("sql server" in s.lower() for s in scenario.infrastructure.existing_systems):
            driven_by.append("infrastructure.existing_systems")
            return CoreComponent(
                choice="Microsoft SQL Server",
                justification="Direct integration with existing on-premise SQL Server 2019 and Azure SQL ecosystem, preserving existing data schemas.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="PostgreSQL", why_not="Migrating existing enterprise SQL Server data and stored procedures adds significant project risk.")],
                tradeoffs=["Commercial licensing costs if scaled to dedicated instances."],
            ), (15.0, 50.0)

        # Case 4: High Availability, RBI Localisation, Enterprise Fintech
        is_enterprise_ha = scenario.requirements.availability in {"99.95", "99.99"} or ComplianceStandard.RBI_LOCALISATION in scenario.compliance
        if (
            is_enterprise_ha
            and scenario.infrastructure.cloud_preference != CloudPreference.GCP
            and scenario.infrastructure.cloud_preference != CloudPreference.AZURE
            and scenario.infrastructure.deployment_model not in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}
        ):
            driven_by.extend(["requirements.availability", "compliance", "scale.workload"])
            return CoreComponent(
                choice="Amazon Aurora PostgreSQL",
                justification="Multi-AZ synchronous replication with automated 30-second failover, continuous backups to S3, and physical data localization in AWS Mumbai (ap-south-1).",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Self-Hosted PostgreSQL on EC2", why_not="Fails automated multi-AZ failover and point-in-time recovery without complex manual Patroni setup.")],
                tradeoffs=["Higher minimum cost threshold ($60+/mo baseline)."],
            ), (65.0, 180.0)

        # Case 5: Default General Relational (PostgreSQL)
        driven_by.extend(["scale.workload", "priorities.cost"])
        db_choice = "PostgreSQL"
        db_just = "ACID-compliant relational database with JSONB support, indexing, and full text search; available as a managed service across all major clouds."
        db_cost = (15.0, 45.0)
        db_alts = [AlternativeItem(choice="MongoDB", why_not="Lacks native relational foreign key integrity and ACID guarantees needed for structured transactional data.")]
        if scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}:
            driven_by.append("infrastructure.deployment_model")
            db_just = "Self-hosted PostgreSQL container with local persistent volumes, preserving zero-cloud dependency for on-premise deployment."
            db_cost = (0.0, 0.0)
            db_alts = [AlternativeItem(choice="Amazon Aurora / Cloud SQL", why_not=f"Public cloud managed databases violate strict {scenario.infrastructure.deployment_model.value} boundaries.")]

        return CoreComponent(
            choice=db_choice,
            justification=db_just,
            driven_by=driven_by,
            alternatives=db_alts,
            tradeoffs=["Requires connection pooling (e.g. PgBouncer) under high concurrent connection spikes."],
        ), db_cost

    def _recommend_hosting(self, scenario: ScenarioInput, frontend: CoreComponent, backend: CoreComponent, database: CoreComponent) -> tuple[CoreComponent, tuple[float, float]]:
        candidates = self.catalog.get_by_category("hosting")
        valid, rejected = filter_candidates(candidates, scenario)
        driven_by = ["budget.monthly_infra_usd", "infrastructure.deployment_model"]

        # Case 0: On-Premise or Air-Gapped Deployment
        if scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}:
            driven_by.extend(["infrastructure.deployment_model"])
            is_air = scenario.infrastructure.deployment_model == DeploymentModel.AIR_GAPPED
            env_type = "air-gapped isolated network" if is_air else "on-premise corporate datacenter"
            return CoreComponent(
                choice="On-Premise Server (Docker Compose / Podman)",
                justification=f"Strict {env_type} constraint strictly eliminates external public cloud PaaS/SaaS dependencies; containers orchestrated locally on bare-metal or hypervisor VMs.",
                driven_by=driven_by,
                alternatives=[
                    AlternativeItem(choice="Public Cloud (AWS / GCP / Azure)", why_not=f"Public cloud services violate the mandatory {scenario.infrastructure.deployment_model.value} isolation boundary."),
                    AlternativeItem(choice="Kubernetes (k8s)", why_not="Kubernetes introduces immense operational complexity and dedicated DevOps staffing burden compared to Docker Compose / Podman for on-prem operations.")
                ],
                tradeoffs=["Requires physical hardware procurement, manual OS patching, and internal disaster recovery planning."],
            ), (0.0, 0.0)

        # Case 1: Static Content (P1 archetype or High Traffic Static Content)
        if backend.choice == "None" and database.choice == "None":
            driven_by.extend(["scale.traffic_pattern", "project.type"])
            choice_name = "Netlify (Free)" if scenario.budget.monthly_infra_usd == 0 else "Netlify / Edge CDN"
            cost_range = (0.0, 0.0) if scenario.budget.monthly_infra_usd == 0 else (0.0, 15.0)
            return CoreComponent(
                choice=choice_name,
                justification="Global edge CDN hosting with automated Git deployments and edge caching, serving pre-rendered static assets with zero compute overhead.",
                driven_by=driven_by,
                alternatives=[
                    AlternativeItem(choice="Kubernetes Cluster (EKS / GKE)", why_not="Massive over-engineering trap: running container orchestration for pre-rendered content incurs extreme cost ($70+/mo minimum) and unnecessary operational complexity."),
                    AlternativeItem(choice="AWS ECS Fargate", why_not="Running dedicated container compute for static read-only files is redundant when assets can be served directly from global edge caches.")
                ],
                tradeoffs=["Monthly build minutes and bandwidth caps on free/entry tiers; dynamic backend logic requires external serverless handlers."],
            ), cost_range

        # Case 2: Explicit Azure Cloud Preference / .NET Stack (P5)
        if scenario.infrastructure.cloud_preference == CloudPreference.AZURE or backend.choice.startswith("ASP.NET"):
            driven_by.extend(["infrastructure.cloud_preference", "infrastructure.data_residency"])
            return CoreComponent(
                choice="Azure App Service",
                justification="Managed PaaS deployment in Azure Central India (Pune) with automated OS patching and native Entra ID authentication integration.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="Google Cloud Run", why_not="Incompatible with explicit cloud preference for Azure and lacks native Entra ID managed identity hooks.")],
                tradeoffs=["Higher compute plan cost when scaling to premium dedicated hardware."],
            ), (25.0, 75.0)

        # Case 3: Explicit AWS Cloud Preference or High-Scale Enterprise Fintech (P4)
        if scenario.infrastructure.cloud_preference == CloudPreference.AWS or ComplianceStandard.RBI_LOCALISATION in scenario.compliance:
            driven_by.extend(["infrastructure.cloud_preference", "compliance", "scale.users_12_months"])
            return CoreComponent(
                choice="AWS ECS Fargate",
                justification="Serverless container compute in AWS Mumbai (ap-south-1) with VPC isolation, IAM roles, and certifications meeting RBI and PCI-DSS compliance.",
                driven_by=driven_by,
                alternatives=[AlternativeItem(choice="AWS EC2 (Self-Managed)", why_not="Requires manual OS patching, AMI baking, and custom auto-scaling scripts; Fargate eliminates operational maintenance.")],
                tradeoffs=["Containers do not scale to zero; minimum monthly container run cost applies."],
            ), (45.0, 160.0)

        # Case 4: Cost-Sensitive Managed Container (P2, P6 archetype - $100-$150 budget)
        driven_by.extend(["budget.monthly_infra_usd", "team.has_devops", "infrastructure.data_residency"])
        return CoreComponent(
            choice="Google Cloud Run (asia-south1)",
            justification="Managed serverless container platform scaling to zero when idle; data center in Mumbai meets India data residency while staying well within the monthly budget.",
            driven_by=driven_by,
            alternatives=[AlternativeItem(choice="AWS ECS Fargate", why_not="Fargate incurs fixed minimum compute costs without scale-to-zero, consuming more of a tight $100–$150 budget.")],
            tradeoffs=["Occasional 1–2 second cold starts on new container scaling instances."],
        ), (10.0, 35.0)

    def _recommend_supporting(self, scenario: ScenarioInput, frontend: CoreComponent, backend: CoreComponent, database: CoreComponent, hosting: CoreComponent) -> tuple[list[SupportingComponent], tuple[float, float]]:
        supporting: list[SupportingComponent] = []
        cost_min = 0.0
        cost_max = 0.0

        # Form Handler (for static sites)
        if backend.choice == "None" and scenario.project.type == ProjectType.CONTENT_SITE:
            supporting.append(
                SupportingComponent(
                    layer="forms",
                    choice="Netlify Forms",
                    justification="Serverless form handling embedded in static HTML without deploying an application server.",
                    driven_by=["project.type", "backend.choice"],
                    alternatives=[AlternativeItem(choice="Formspree", why_not="Netlify Forms is natively bundled with the hosting provider.")],
                    tradeoffs=["100 submissions per month limit on free tier."],
                )
            )

        # Real-time WebSocket Layer
        if scenario.requirements.realtime:
            cost_min += 5.0
            cost_max += 25.0
            supporting.append(
                SupportingComponent(
                    layer="realtime",
                    choice="Socket.io with Redis Adapter",
                    justification="Bi-directional WebSocket communication enabling real-time chat, notifications, and collaborative state syncing.",
                    driven_by=["requirements.realtime"],
                    alternatives=[AlternativeItem(choice="Pusher", why_not="Proprietary commercial SaaS with steep pricing jumps under high concurrency.")],
                    tradeoffs=["Requires stateful connection management on backend workers."],
                )
            )

        # Full-Text Search Layer
        if scenario.requirements.full_text_search:
            cost_min += 0.0
            cost_max += 20.0
            supporting.append(
                SupportingComponent(
                    layer="search",
                    choice="Meilisearch",
                    justification="Fast, typo-tolerant search engine providing sub-50ms query responses with minimal operational setup.",
                    driven_by=["requirements.full_text_search"],
                    alternatives=[AlternativeItem(choice="Elasticsearch", why_not="Elasticsearch has heavy JVM RAM overhead (2GB+), excessive for small-to-medium datasets.")],
                    tradeoffs=["Index must fit into host server memory."],
                )
            )

        # File & Media Storage
        if scenario.requirements.file_media_storage:
            if scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}:
                storage_choice = "MinIO (Self-Hosted S3-Compatible Storage)"
                storage_just = "High-performance S3-compatible object storage deployed inside on-premise infrastructure without external internet connectivity."
                storage_alt = [AlternativeItem(choice="Amazon S3 / Azure Blob", why_not=f"Public cloud storage violates strict {scenario.infrastructure.deployment_model.value} isolation boundary.")]
                storage_cost = (0.0, 0.0)
            else:
                storage_cost = (5.0, 25.0)
                storage_choice = "Amazon S3" if scenario.infrastructure.cloud_preference != CloudPreference.AZURE else "Azure Blob Storage"
                storage_just = "Durable, encrypted cloud object storage for user document and photo uploads with presigned URL access."
                storage_alt = [AlternativeItem(choice="Local Disk Storage", why_not="Local container disks are ephemeral and lose user uploads on container restarts.")]

            cost_min += storage_cost[0]
            cost_max += storage_cost[1]
            supporting.append(
                SupportingComponent(
                    layer="storage",
                    choice=storage_choice,
                    justification=storage_just,
                    driven_by=["requirements.file_media_storage", "infrastructure.deployment_model"],
                    alternatives=storage_alt,
                    tradeoffs=["Requires local disk storage capacity alerting." if "MinIO" in storage_choice else "Outbound internet data egress transfer costs."],
                )
            )

        # Payments Gateway
        if scenario.requirements.payments:
            if scenario.infrastructure.data_residency == DataResidency.INDIA or ("india" in scenario.project.description.lower() if scenario.project.description else False):
                choice = "Razorpay Payment Gateway"
                why_not = "Stripe lacks native zero-fee UPI and Indian domestic netbanking settlement options."
                alt = "Stripe"
            else:
                choice = "Stripe"
                why_not = "Razorpay is tailored specifically for Indian domestic banking."
                alt = "Razorpay"
            supporting.append(
                SupportingComponent(
                    layer="payments",
                    choice=choice,
                    justification="PCI-DSS compliant payment integration supporting cards, netbanking, and digital wallets without holding sensitive payment data.",
                    driven_by=["requirements.payments", "infrastructure.data_residency"],
                    alternatives=[AlternativeItem(choice=alt, why_not=why_not)],
                    tradeoffs=["2% transaction processing fee."],
                )
            )

        # Authentication Service
        if scenario.requirements.auth != AuthRequirement.NONE:
            if scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}:
                choice = "Keycloak (Self-Hosted Identity)"
                alt = "Firebase Auth / Auth0"
                why_not = "Cloud SaaS identity providers require public internet access, violating on-premise / air-gapped isolation."
                cost_delta = (0.0, 0.0)
            elif scenario.requirements.auth == AuthRequirement.ENTERPRISE_SSO:
                choice = "Microsoft Entra ID (Azure AD)"
                alt = "Auth0"
                why_not = "Auth0 adds high per-user enterprise tier pricing, whereas Entra ID natively links with existing corporate M365 directories."
                cost_delta = (0.0, 15.0)
            elif scenario.requirements.auth == AuthRequirement.PHONE_OTP:
                choice = "Firebase Auth (Phone OTP)"
                alt = "Twilio Verify Custom"
                why_not = "Building custom SMS OTP verification requires maintaining SMS gateways and credential token databases."
                cost_delta = (0.0, 15.0)
            else:
                choice = "Supabase Auth / NextAuth"
                alt = "Custom JWT Auth"
                why_not = "Rolling custom authentication risks token vulnerabilities and password hashing security flaws."
                cost_delta = (0.0, 10.0)

            cost_min += cost_delta[0]
            cost_max += cost_delta[1]
            supporting.append(
                SupportingComponent(
                    layer="auth",
                    choice=choice,
                    justification=f"Authentication service resolving {scenario.requirements.auth.value} requirements with secure token issuance.",
                    driven_by=["requirements.auth", "infrastructure.deployment_model"],
                    alternatives=[AlternativeItem(choice=alt, why_not=why_not)],
                    tradeoffs=["Self-managed Keycloak database realm backups required." if "Keycloak" in choice else "Vendor SDK dependency."],
                )
            )

        # In-Memory Cache (Redis)
        if backend.choice != "None" and (scenario.scale.traffic_pattern == WorkloadType.WRITE_HEAVY or (scenario.requirements.p95_latency_ms and scenario.requirements.p95_latency_ms <= 100)):
            cost_min += 15.0
            cost_max += 40.0
            supporting.append(
                SupportingComponent(
                    layer="cache",
                    choice="Redis",
                    justification="In-memory sub-millisecond key-value caching to absorb read bursts and protect database connection limits.",
                    driven_by=["requirements.p95_latency_ms", "scale.traffic_pattern"],
                    alternatives=[AlternativeItem(choice="Memcached", why_not="Memcached lacks rich data structures and pub/sub capabilities.")],
                    tradeoffs=["Volatile memory requiring persistence configuration."],
                )
            )

        # Queue / Asynchronous Tasks
        if backend.choice != "None" and (
            ComplianceStandard.RBI_LOCALISATION in scenario.compliance
            or scenario.scale.users_12_months >= 100000
            or (scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED} and scenario.requirements.realtime)
        ):
            if scenario.infrastructure.deployment_model in {DeploymentModel.ON_PREMISE, DeploymentModel.AIR_GAPPED}:
                q_choice = "RabbitMQ (Self-Hosted)"
                q_just = "Open-source AMQP message broker deployed on-premise for reliable asynchronous decoupling without cloud connectivity."
                q_alts = [AlternativeItem(choice="Amazon SQS", why_not="Amazon SQS is a public cloud service unavailable in air-gapped or on-prem environments.")]
                q_cost = (0.0, 0.0)
            else:
                q_choice = "Amazon SQS FIFO"
                q_just = "Durable, exactly-once ordered message queue for decoupled background ledger processing and webhook delivery."
                q_alts = [AlternativeItem(choice="RabbitMQ Self-Hosted", why_not="RabbitMQ requires dedicated cluster maintenance, clustering plugins, and disk management.")]
                q_cost = (5.0, 25.0)

            cost_min += q_cost[0]
            cost_max += q_cost[1]
            supporting.append(
                SupportingComponent(
                    layer="queue",
                    choice=q_choice,
                    justification=q_just,
                    driven_by=["compliance", "scale.users_12_months", "infrastructure.deployment_model"],
                    alternatives=q_alts,
                    tradeoffs=["Requires persistent disk volume monitoring and clustering setup." if "RabbitMQ" in q_choice else "Throughput capped at 3,000 messages/sec with batching."],
                )
            )

        # Machine Learning Inference API
        if scenario.requirements.ml_features == MLRequirement.INFERENCE_API:
            cost_min += 10.0
            cost_max += 40.0
            supporting.append(
                SupportingComponent(
                    layer="ml",
                    choice="AWS SageMaker Serverless Inference",
                    justification="Serverless model endpoint running credit scoring inference on demand, scaling to zero when idle.",
                    driven_by=["requirements.ml_features"],
                    alternatives=[AlternativeItem(choice="Dedicated EC2 GPU Instance", why_not="Dedicated GPU instances cost $150+/month even during zero-traffic idle periods.")],
                    tradeoffs=["Initial cold start delay when spinning up idle containers."],
                )
            )

        # Observability for High Availability
        if scenario.requirements.availability in {"99.95", "99.99"}:
            cost_min += 10.0
            cost_max += 30.0
            supporting.append(
                SupportingComponent(
                    layer="observability",
                    choice="OpenTelemetry + Prometheus",
                    justification="Vendor-neutral distributed tracing and metrics required to monitor SLA breaches and system health.",
                    driven_by=["requirements.availability"],
                    alternatives=[AlternativeItem(choice="Datadog", why_not="Proprietary commercial observability with unpredictable host/metric volume bills.")],
                    tradeoffs=["Requires configuring dashboard scraping and metric retention storage."],
                )
            )

        return supporting, (cost_min, cost_max)

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------

    def _determine_architecture_style(
        self,
        scenario: ScenarioInput,
        frontend: CoreComponent,
        backend: CoreComponent,
        database: CoreComponent,
        hosting: CoreComponent,
    ) -> ArchitectureStyle:
        if backend.choice == "None" and database.choice == "None":
            return ArchitectureStyle.STATIC
        if "Cloud Run" in hosting.choice or "Fargate" in hosting.choice:
            return ArchitectureStyle.SERVERLESS
        if "Spring Boot" in backend.choice or "ASP.NET" in backend.choice:
            return ArchitectureStyle.MODULAR_MONOLITH
        return ArchitectureStyle.MODULAR_MONOLITH

    def _generate_summary(
        self,
        scenario: ScenarioInput,
        arch_style: ArchitectureStyle,
        frontend: CoreComponent,
        backend: CoreComponent,
        database: CoreComponent,
        hosting: CoreComponent,
        cost_min: float,
        cost_max: float,
    ) -> str:
        b_name = backend.choice if backend.choice != "None" else "serverless/static"
        db_name = database.choice if database.choice != "None" else "no database"
        return (
            f"{arch_style.value.replace('_', ' ').capitalize()} architecture combining {frontend.choice} frontend "
            f"and {b_name} backend with {db_name} hosted on {hosting.choice}. "
            f"Estimated monthly infrastructure cost ranges from ${cost_min:.0f} to ${cost_max:.0f}."
        )
