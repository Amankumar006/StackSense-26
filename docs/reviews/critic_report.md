# Stage 7 Critic Review Report

- **Target Document**: `docs/product.md` (lines 1–68)
- **Reviewers**: Design Critic (`egm-design`), Structural Validator (`egm-structural`), Style Reviewer (`egm-style`)
- **Document Standard**: `resources/document_standards/feature-spec-standard.md`
- **Baseline Context**: `docs/official-problem-statement.txt` / `docs/official-problem-statement.pdf`

---

## 1. Executive Summary & Verdict

**Verdict**: **FAIL (Blocked)**  
The document functions as an early concept brief rather than a compliant, complete Feature Specification. It is blocked on three structural and design omissions mandated by the Feature Specification Standard and the official Synergy '26 problem statement:
1. Complete absence of a **Proposed Architecture** section detailing system pipelines, engine components, and knowledge base structures.
2. Complete absence of the mandatory **Evaluation of Alternatives** comparing architectural/algorithmic strategies (e.g., pure LLMs vs. decision trees vs. CSP vs. multi-criteria decision graphs).
3. Complete absence of an internal **Risks, Limits & Mitigations** section covering system-level failure modes, combinatorial scaling, platform determinism drift, and zero-paid-key compliance.

Additionally, the brief misclassifies hard vs. soft constraints, assumes an interactive conversational loop that conflicts with the official headless JSON scenario runner (FR2, Section 3.2), and lists speculative out-of-scope outputs.

---

## 2. Consolidated Findings by Category

### A. Structural Gaps (Feature Specification Standard)

#### Finding 1: Missing Required Section: "Proposed Architecture"
- **Severity**: 🔴 Blocker
- **Reviewers**: `egm-structural`, `egm-design`
- **Affected Scope**: Missing top-level section
- **Discrepancy Description**: The document fails the Feature Specification Standard's mandate for component layout, internal data flows, and ecosystem interfaces. It defines user-facing inputs and outputs but provides no internal system blueprint:
  - No multi-stage pipeline stages (Intake Normalizer $\to$ Hard Constraint Filter $\to$ Compatibility Graph Filter $\to$ Multi-Objective Scoring $\to$ Rationale & Alternative Generator $\to$ JSON Serializer).
  - No data model or storage specification for the technology knowledge catalogue.
  - No interface boundaries separating the headless scenario engine from optional UI adapters.
- **Actionable Recommendation**: Add a dedicated `## Proposed Architecture` section documenting pipeline stages, data flow, knowledge catalogue structures, and CLI/UI interfaces.

#### Finding 2: Missing Required Section: "Alternatives Considered"
- **Severity**: 🔴 Blocker
- **Reviewers**: `egm-structural`, `egm-design`
- **Affected Scope**: Missing top-level section
- **Discrepancy Description**: The document fails the mandatory Alternatives Rule. It outlines a single approach without proving alternative architectures were considered and rejected:
  - *Pure LLM Prompting:* Violates §5.1 rules and incurs a zero score if an LLM selects the stack.
  - *Hardcoded Decision Trees:* Brittle and susceptible to combinatorial explosion across 16 project types and 11 supporting services.
  - *Pure Constraint Satisfaction (SAT/SMT solver):* Guarantees binary feasibility but lacks graded ranking, nuance, and explicit trade-off explanations.
  - *Two-Stage Hybrid (Hard Constraint Filter + Multi-Objective Scored Graph):* Explainable, deterministic, and fully compliant with §5.1.
- **Actionable Recommendation**: Add an `## Alternatives Considered` section documenting these comparisons and defending the hybrid constraint/scoring design.

#### Finding 3: Missing Required Section: "Risks, Limits & Mitigations"
- **Severity**: 🔴 Blocker
- **Reviewers**: `egm-structural`, `egm-design`
- **Affected Scope**: Missing top-level section
- **Discrepancy Description**: Line 53 mentions returning risks to the end user about their stack, but the document contains zero risk analysis for the StackSense engine itself:
  - *Combinatorial Permutation Explosion:* Generating cross-products across frontend, backend, database, hosting, and 11 supporting services without early pruning risks exceeding the 10s latency SLA.
  - *LLM-Off Evaluation Failure:* Section 5.1 requires an engine switch that disables all LLMs and produces the exact same stack.
  - *Float Drift:* Cross-platform floating-point differences in tie-breakers risk violating FR9 (strict determinism).
  - *Zero-Paid-Key Constraint:* Section 2.2 mandates running locally without paid API keys.
- **Actionable Recommendation**: Add an `## Engineering Risks & Mitigations` section addressing system performance limits, memory bounds, deterministic tie-breakers, and zero-paid-key execution.

#### Finding 4: Structural Asymmetry: "Goals & Non-Goals"
- **Severity**: 🟡 Major
- **Reviewers**: `egm-structural`
- **Affected Scope**: Lines 7–9 (`## Objective`) & Lines 56–62 (`## Non-goals for v1`)
- **Discrepancy Description**: The document pairs a high-level `## Objective` with a separated `## Non-goals for v1`, omitting a concrete, structured `## Goals` section.
- **Actionable Recommendation**: Consolidate into an explicit `## Goals & Non-Goals` section with symmetrical, measurable bullet items.

---

### B. Architectural & Domain Alignment Gaps (Official Problem Statement)

#### Finding 5: Misclassification of Hard vs. Soft Constraints
- **Severity**: 🟡 Major
- **Reviewers**: `egm-design`
- **Affected Scope**: Line 17 (`## Product principles`)
- **Discrepancy Description**: Line 17 lumps budget ceilings and availability requirements into hard constraints. Section 5.3 strictly distinguishes:
  - **Hard Constraints:** `data_residency`, `compliance`, `deployment_model`, and explicit `cloud_preference`. Violations must never be produced silently and must yield `status: "infeasible"` or critical warnings.
  - **Soft Constraints:** `budget`, `timeline`, and `priorities`. The engine trades them off and generates `status: "ok_with_warnings"` with documented relaxation assumptions.
- **Actionable Recommendation**: Reclassify constraint tiers to match §5.3, defining deterministic relaxation behavior for soft constraints.

#### Finding 6: Interactive Conversational Loop Conflicts with Batch Scenario Runner
- **Severity**: 🟡 Major
- **Reviewers**: `egm-design`, `egm-style`
- **Affected Scope**: Lines 25–31 (`## Core user journey`), Line 54 (`## Outputs`)
- **Discrepancy Description**: Steps 2–3 assume an interactive session asking adaptive questions. Competition evaluation uses automated headless batch execution importing JSON scenario files (P1–P6 and hidden edge cases). An engine halting for interactive dialogue fails automated testing.
- **Actionable Recommendation**: Define two execution interfaces: (1) Headless / Scenario Import Mode (mandatory, fills optional fields with documented defaults into `assumptions[]`), and (2) Interactive Mode (UI wizard layered on top).

#### Finding 7: Informal Input/Output Lists vs. Binding JSON Schemas
- **Severity**: 🟡 Major
- **Reviewers**: `egm-design`, `egm-style`
- **Affected Scope**: Lines 32–55 (`## Inputs to collect`, `## Outputs`)
- **Discrepancy Description**: Tables list qualitative summaries rather than binding to the 8 official namespaces in Section 3.1 and the output fields in Section 4. Omitted official taxonomies include the 12 supporting service layers and 8 architecture styles.
- **Actionable Recommendation**: Anchor directly to Section 3.1 and Section 4 JSON schemas, defining explicit validation error behavior (`status: "invalid_input"`).

---

### C. Technical Style, Editorial Precision & Tone

#### Finding 8: Uncalibrated Defensive Caveat Weakening Mandatory Requirement
- **Severity**: 🟡 Major
- **Reviewers**: `egm-style`
- **Affected Scope**: Line 53 (`## Outputs`)
- **Style Rationale**: `"and at least one viable alternative where feasible"` introduces an uncalibrated caveat. Section 2.1 (FR5) and Section 4 strictly mandate $\ge 1$ alternative for each of the four core layers.
- **Editorial Action**: `CALIBRATE`. Strike `"where feasible"` and state: `"Key risks, trade-offs, and at least one viable alternative for each of the four core layers (per FR5)."`

#### Finding 9: Out-of-Scope Artifact ("migration notes")
- **Severity**: 🟡 Major
- **Reviewers**: `egm-style`
- **Affected Scope**: Line 30 (`## Core user journey`, Step 5)
- **Style Rationale**: `"migration notes"` introduces an ungrounded output artifact absent from the Section 4 schema.
- **Editorial Action**: `DROP` or `CALIBRATE` to match the Section 4 output payload.

#### Finding 10: Hackathon Meta-Commentary in Success Measures
- **Severity**: 🟡 Major
- **Reviewers**: `egm-style`, `egm-design`
- **Affected Scope**: Line 68 (`## Success measures`)
- **Style Rationale**: `"The final submission visibly addresses public and hidden scenarios..."` uses subjective contest meta-language rather than verifiable system criteria.
- **Editorial Action**: `CALIBRATE`. Reframe as: `"The engine processes all public and hidden benchmark scenarios, returning 'infeasible' status with critical warnings for impossible constraints, and resolving incomplete inputs via documented assumptions."` Also incorporate the official 4-part scoring rubric (35/30/20/15).

#### Finding 11: Editorial Precision and Fluff Stripping
- **Severity**: 🟢 Nit
- **Reviewers**: `egm-style`
- **Affected Scope**: Lines 5, 9, 13, 26
- **Style Rationale**:
  - Line 5: Replace `"cheap and fast for a student prototype"` with `"low-cost, rapid-delivery prototype"`.
  - Line 9: Strip promotional adjective `"intelligent"`; replace with `"deterministic recommendation engine"`.
  - Line 13: Replace startup jargon `"builder"` with `"software engineer, architect, technical lead, or student"`.
  - Line 26: Replace colloquialism `"high-signal questions"` with `"mandatory baseline project parameters"`.
