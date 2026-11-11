# Product Specification — StackSense

**Project:** StackSense Challenge · Synergy '26 (IIIT Bangalore)  
**Status:** Reconciled to Official Problem Statement (v1.0, 10 November 2026)  
**Authority:** Official Unstop Problem Statement & Contract Specifications

---

## 1. Problem Statement

Selecting a software technology stack is a constrained, multi-objective engineering optimization problem. A stack suitable for a low-cost, rapid-delivery prototype (e.g., student MVP with zero budget) can be fundamentally inappropriate or illegal for an enterprise fintech bound by regulatory data residency, or a real-time collaborative tool chasing sub-100ms latency.

Standard practitioner approaches rely on informal developer intuition, static blog recommendations, or popularity surveys that fail to:
- Enforce non-negotiable regulatory, regional, or deployment constraints before preferences.
- Evaluate cross-component interoperability (e.g., pairing serverless functions with long-lived connection pools).
- Transparently explain *why* specific components won, which input constraints drove the choice, and *why* plausible alternatives were rejected.
- Gracefully handle budget and timeline trade-offs without either failing completely or ignoring the limits.

---

## 2. Objective & Product Goals

Build a **deterministic, explainable technology stack recommendation engine** that evaluates structured project parameters (scale, team experience and languages, budget, timeline, infrastructure, requirements, and compliance obligations) and outputs a justified, compatible architecture: **frontend**, **backend**, **database**, **hosting**, and **supporting services**.

### In-Scope Functional Goals (FR1–FR9)
- **FR1 (Input Collection):** Accept all mandatory and optional parameters in Section 3 through an interactive form and CLI.
- **FR2 (Scenario Import):** Ingest scenarios from standard JSON files in a single pass for automated grading and benchmark testing.
- **FR3 (Core Recommendation):** Output one justified selection for each core layer (`frontend`, `backend`, `database`, `hosting`), allowing `"None"` when structurally justified (e.g., static sites).
- **FR4 (Supporting Services):** Conditionally recommend auxiliary services across 12 official layers (`cache`, `queue`, `search`, `auth`, `storage`, `cdn`, `realtime`, `payments`, `ml`, `ci_cd`, `observability`, `other`) based on explicit requirements.
- **FR5 (Component Explainability):** For every recommended component, provide an architectural justification, the input field paths that drove the choice (`driven_by`), at least one viable alternative with a concrete rejection reason (`why_not`), and known trade-offs.
- **FR6 (Cost Estimation):** Provide an order-of-magnitude monthly infrastructure cost band in USD (`{min, max, assumptions[]}`) based on published provider pricing units and free tiers.
- **FR7 (Validation & Conflict Resolution):** Perform schema validation returning field-level errors (`status: "invalid_input"`). Detect contradictory constraints, emitting critical warnings and generating either an infeasible verdict (`status: "infeasible"`) or a relaxed stack with documented compromises (`status: "ok_with_warnings"`).
- **FR8 (JSON Output Export):** Export recommendations conforming strictly to the official Section 4 schema.
- **FR9 (Deterministic Repeatability):** Guarantee identical outputs for identical inputs across runs and platforms.

### Non-Goals for v1
- **No Core LLM Decision-Making:** Relying on LLMs for technology selection or constraint evaluation is strictly prohibited (violates §5.1; incurs zero score for Recommendation Quality). LLMs are restricted to optional input parsing and explanation polish.
- **No Multi-Turn Conversational Interviewing in Scenario Execution:** Automated grading operates headlessly via JSON import. Interactive conversational back-and-forth is a non-goal for core scenario processing.
- **No Production Code or IaC Generation:** Generating application scaffolding, Terraform scripts, Dockerfiles, or Kubernetes manifests is out of scope.
- **No Live Billing API Scrapers:** Providing exact, real-time cloud invoice quotes is out of scope; cost estimates are order-of-magnitude bands based on published baselines.
- **No Legal Compliance Certification:** StackSense enforces documented architectural suitability facts, but does not substitute for formal security or legal certification.

---

## 3. Product Principles

1. **Hard Constraints Override Popularity (§5.3):**  
   `data_residency`, `compliance`, `deployment_model`, and explicit `cloud_preference` are absolute invariant boundaries. A stack that violates these constraints must never be produced silently.
2. **Soft Constraints Are Dynamically Balanced (§5.3):**  
   `budget`, `timeline`, and `priorities` (cost, time to market, scalability, performance, maintainability, security) are optimization criteria. When tight budgets or timelines conflict with scale goals, the engine trades them off, relaxes soft constraints deterministically, and issues `status: "ok_with_warnings"` with documented relaxation notes in `assumptions[]`.
3. **Stacks, Not Isolated Tools:**  
   Components are evaluated for cross-layer interoperability, operational complexity, and team fit using an explicit compatibility graph.
4. **Mandatory Explainability & Traceability:**  
   Every recommendation must defend itself. A component choice without input field traceability (`driven_by`) and rejected alternatives (`why_not`) is considered incomplete.
5. **Surface Uncertainty & Defaults Explicitly:**  
   Omitted optional inputs are never silently fabricated; they are resolved using documented defaults recorded in the output `assumptions[]`.
6. **Zero-Paid-Key, Offline-First Execution (§2.2):**  
   The engine runs locally out of the box in $<15$ minutes without requiring external paid API keys, network access, or SaaS tokens.

---

## 4. Execution Modalities

### Primary: Headless Batch Scenario Runner (Mandatory for Grading)
The primary execution path is a single-pass CLI command that ingests a scenario JSON file (e.g., `data/scenarios/P2.json`) and exports the standard result JSON:
```bash
python -m stacksense.cli run data/scenarios/P2.json --output outputs/P2_output.json --no-llm
```
- Missing optional fields are populated with documented defaults recorded in `assumptions[]`.
- Invalid fields yield `status: "invalid_input"` with `validation_errors[]` and `stack: null`.
- Unresolvable hard constraints yield `status: "infeasible"` with critical `warnings[]`.

### Secondary: Interactive Intake Form
A lightweight UI/form that guides a human user through the 8 input namespaces, performs real-time validation, and exports compliant scenario JSON.

---

## 5. Input & Output Contract Baseline

### Input Contract (Section 3.1)
The engine accepts 8 structured namespaces:
1. `project`: `name`, `type` (16 standard enums), `description`, `platforms` (`web`, `android`, `ios`, `desktop`, `api_only`).
2. `scale`: `users_at_launch`, `users_12_months`, `peak_concurrent_users`, `traffic_pattern` (`steady`, `spiky`, `seasonal`), `workload` (`read_heavy`, `balanced`, `write_heavy`), `data_volume_gb_12_months`.
3. `team`: `size`, `experience` (`beginner`, `intermediate`, `senior`, `mixed`), `languages` (list of strings), `has_devops` (boolean).
4. `budget`: `monthly_infra_usd` (number $\ge 0$).
5. `timeline`: `mvp_weeks` (integer $\ge 1$).
6. `infrastructure`: `cloud_preference` (`any`, `aws`, `gcp`, `azure`, `none`), `deployment_model` (`managed_cloud`, `self_hosted_cloud_vm`, `on_premise`, `air_gapped`), `data_residency` (`none`, `india`, `eu`, `us`, `other`), `existing_systems` (list of strings).
7. `requirements`: `realtime`, `offline_support`, `full_text_search`, `file_media_storage`, `payments`, `auth` (enum), `multi_tenant`, `ml_features` (enum), `seo_critical`, `availability` (enum string), `p95_latency_ms`.
8. `compliance`: list of enums (`gdpr`, `dpdp`, `hipaa`, `pci_dss`, `rbi_localisation`, `soc2`, `iso27001`).
9. `priorities`: 1–5 weights for `cost`, `time_to_market`, `scalability`, `performance`, `maintainability`, `security`.

### Output Contract (Section 4)
The engine emits standard JSON containing:
- `status`: `"ok"` | `"ok_with_warnings"` | `"infeasible"` | `"invalid_input"`
- `summary`: One or two sentences describing the architecture.
- `architecture_style`: `"static"` | `"monolith"` | `"modular_monolith"` | `"serverless"` | `"service_oriented"` | `"microservices"` | `"hybrid"` | `"other"`
- `stack`:
  - `frontend`, `backend`, `database`, `hosting`: `{ choice, justification, driven_by: [], alternatives: [{choice, why_not}], tradeoffs: [] }`
  - `supporting[]`: list of `{ layer, choice, justification, driven_by: [], alternatives: [], tradeoffs: [] }`
- `estimated_monthly_cost_usd`: `{ min, max, assumptions: [] }`
- `warnings[]`: list of `{ code, severity: "info" | "warning" | "critical", message, fields: [] }`
- `assumptions[]`: list of strings (defaults or interpretations applied)
- `validation_errors[]`: list of `{ field, message }`

---

## 6. High-Level Proposed Architecture

```text
                     ┌──────────────────────────────────────────────┐
                     │         Scenario Input (CLI / UI Form)       │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 1. Schema Validator & Normalizer             │
                     │    - Validates types, ranges, enums          │
                     │    - Assigns documented defaults             │
                     │    - Detects field errors & contradictions   │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 2. Hard-Constraint Evaluator                 │
                     │    - Prunes by residency, compliance, model  │
                     │    - Flags hard exclusions / infeasibility   │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 3. Layer Scorer & Compatibility Composer     │
                     │    - Evaluates technology catalogue records  │
                     │    - Multi-objective weighted utility scoring│
                     │    - Cross-layer compatibility validation    │
                     │    - Soft-constraint trade-off & relaxation  │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 4. Explanation & Cost Estimator              │
                     │    - Extracts driven_by field paths          │
                     │    - Selects top alternative + why_not reason│
                     │    - Computes order-of-magnitude cost band   │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 5. JSON Serializer & Report Exporter         │
                     │    - Emits strict Section 4 JSON output      │
                     └──────────────────────────────────────────────┘
```

The technology knowledge base is maintained as a **versioned, static catalogue in the repository** (`data/technology-catalog/`), with verified metadata, limits, costs, and primary-source citations for at least 6–8 realistic technologies per core layer. Technical pipeline details are specified in [`docs/design.md`](design.md).

---

## 7. Alternatives Considered

| Alternative Architectural Approach | Technical Trade-off / Evaluation | Status |
| :--- | :--- | :--- |
| **Pure LLM Generation (Prompt Engineering)** | Prohibited by §5.1. Produces hallucinations, non-deterministic choices, and receives zero marks in competition evaluation. | **Rejected** |
| **Hardcoded Decision Trees** | Extremely brittle; combinatorial explosion across 16 project types $\times$ 11 supporting services $\times$ diverse team skill profiles. Fails to generate dynamic alternatives or transparent weighted scoring. | **Rejected** |
| **Pure SMT/SAT Constraint Solver** | Guarantees binary satisfiability, but lacks graded architectural nuance, multi-attribute ranking, and natural component justifications. High dependency overhead. | **Rejected** |
| **Two-Stage Hybrid Engine (Constraint Pruning + Weighted Multi-Criteria Graph)** | Deterministic, highly auditable, evaluates hard constraints strictly before scoring, ranks alternatives with clear numerical deltas, runs in $<100$ms, and strictly complies with §5.1. | **Chosen** |

---

## 8. Engineering Limits & Non-Functional Requirements

- **Execution Latency:** Complete scenario execution in $\le 10$ seconds on a standard laptop (target $< 1$s).
- **Setup Time:** Zero external database dependencies; runnable via standard Python 3.11+ virtual environment or Docker in under 15 minutes.
- **Zero Paid Dependencies:** Operates 100% offline without requiring paid API keys or commercial SaaS tokens.
- **Deterministic Reliability:** Discrete integer priority weights and stable alphabetical tie-breaking eliminate floating-point drift across platforms.
- **LLM-Off Guarantee:** An explicit `--no-llm` flag or `ENABLE_LLM=false` environment variable guarantees identical stack recommendations.

---

## 9. Evaluation Rubric & Success Measures

StackSense measures success directly against the official competition evaluation criteria (§8):

1. **Recommendation Quality (35%):**
   - Correctness across public benchmark scenarios (`P1` through `P6`) and automated hidden test scenarios.
   - Zero violations of hard constraints (`data_residency`, `compliance`, `deployment_model`, `cloud_preference`).
   - Anti-overengineering: Avoids microservices or Kubernetes for simple workloads (e.g., P1 DevFolio).
   - Identical recommendations verified under the LLM-off switch.
2. **Input Design & Research (30%):**
   - 100% compliance with Section 3.1 schema fields, types, and enums.
   - Comprehensive edge-case handling for missing fields, invalid ranges, and contradictory requirements.
   - Depth and accuracy of the technology catalogue with primary-source citations.
3. **Reasoning & Explainability (20%):**
   - Every choice has a clear, non-generic justification with input-linked `driven_by` field paths.
   - At least one viable alternative with a concrete, comparative `why_not` explanation for each core layer.
   - Clear, plain-language warnings for risks and relaxed constraints.
4. **Documentation Quality (15%):**
   - Copy-paste local runbook in `README.md` verified under 15 minutes.
   - Comprehensive project report conforming strictly to the official 10-section template ($\le 15$ pages).
