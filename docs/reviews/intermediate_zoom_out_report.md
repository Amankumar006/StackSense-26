# Stage 8 Intermediate Zoom Out Review Report

- **Target Document**: `docs/product.md` (lines 1–68)
- **Reviewer**: Skeptical Architect (`egm-zoom-out`)
- **Document Standard**: `resources/document_standards/zoom-out-standard.md`
- **Baseline Context**: `docs/official-problem-statement.txt` / `docs/official-problem-statement.pdf`, `zoom_out_report.md`, `comprehension_report.md`, `critic_report.md`

---

## 1. Executive Architectural Assessment

Following the Stage 6 Comprehension Test and Stage 7 Critic Review, `docs/product.md` requires targeted updates to align with the official Synergy '26 problem statement. However, a major architectural risk emerged from earlier review recommendations: **reviewers attempted to turn this high-level product brief into a bloated implementation document**, demanding formal SAT/SMT solvers, combinatorial graph-traversal machinery, dynamic multi-turn conversational agents, and floating-point normalization libraries.

As the Skeptical Architect, the mandate is to enforce **extreme simplicity, anti-YAGNI, and strict altitude control**. The root problem is straightforward:
> *Given a structured JSON scenario describing project scale, team skills, compliance rules, and budget, deterministically filter out invalid technologies, score viable candidates per layer, assemble a compatible stack, and output a structured JSON explanation that a senior engineer would accept, running locally in <10 seconds without paid API keys.*

---

## 2. Skeptical Audit of Prior Recommendations (Bloat & Over-Engineering Checks)

### Finding 1: Scope Inflation & Document Identity Confusion
- **Severity**: 🔴 **Blocker**
- **Affected Scope**: Overall Document Structure & Critic Findings 1–3
- **Simplicity Rationale**: The Stage 7 Critic demanded inserting a multi-stage pipeline specification, data model storage definitions, algorithmic trade-off matrices, and failure mitigation logs into `docs/product.md`.
  - In our workspace, `docs/design.md` already exists specifically as the technical system design document.
  - Forcing `docs/product.md` to duplicate low-level pipeline mechanics or data storage specs creates redundant documentation bloat and blurs the boundary between product requirements and system implementation.
  - **Simplification**: `docs/product.md` must remain at the product requirement altitude (what the engine delivers, contract compliance, inputs, outputs, UX, and non-goals). It should include a high-level, 1-paragraph architecture summary and a conceptual alternatives summary, cleanly delegating technical mechanics to `docs/design.md`.

### Finding 2: Algorithmic Over-Engineering (Speculative SAT/SMT Solvers & Graph Traversals)
- **Severity**: 🟡 **Major**
- **Affected Scope**: Critic Finding 2 & Inventive Catalyst Finding 3
- **Simplicity Rationale**: Prior reviews proposed treating stack selection as a complex constraint satisfaction problem requiring SAT/SMT solvers or an "Intermediary Compatibility Graph" to combat "combinatorial permutation explosion across 11 supporting services."
  - This is classic premature optimization. The official problem statement FAQ (§12) specifies that a credible engine knows ~6–8 realistic options per core layer (frontend, backend, database, hosting). Supporting services (cache, auth, payments, search, etc.) are selected conditionally based on explicit boolean input flags (`requirements.payments -> payments`), NOT through an unconstrained 16-dimensional cartesian cross-product.
  - A clean, 2-phase deterministic pipeline—(1) Hard constraint filtering, followed by (2) Weighted utility scoring per layer with direct pairwise compatibility checks—solves the problem in under 100 milliseconds, requires zero heavyweight external solver libraries, and is 100% auditable.

### Finding 3: Interactive Conversational / Adaptive Dialogue Bloat
- **Severity**: 🟡 **Major**
- **Affected Scope**: `## Core user journey` (lines 24–31), `## Product principles` (line 20), Critic Finding 6
- **Simplicity Rationale**: Both existing text and prior review notes suggest building an "adaptive questioning controller" that conducts multi-turn interactive interviews to narrow down requirements.
  - This violates YAGNI and the competition evaluation reality: the engine is evaluated primarily via headless, single-pass automated execution importing JSON scenario files (P1–P6 and hidden judge scenarios; see FR2, §3.2, §8, §9.4). An automated grading script cannot engage in a multi-turn chat.
  - Missing optional fields must simply be resolved in a single pass using documented defaults recorded in `assumptions[]`.
  - The v1 UI should be a simple single-page input form or JSON uploader. Designing a dynamic conversational engine or branching survey dialogue is out-of-scope over-engineering.

### Finding 4: Knowledge Base Infrastructure Bloat
- **Severity**: 🟡 **Major**
- **Affected Scope**: Comprehension Finding 1 & Critic Finding 1
- **Simplicity Rationale**: Comprehension correctly noted that "catalogue" was undefined, and Critic called for data storage specifications. If interpreted as needing an external SQL database, vector database, or dynamic CMS API, this would violate Section 2.2 ("Runs locally from your README... under 15 minutes", "No paid keys required").
  - The simplest, most reproducible, zero-maintenance architecture is a **static, versioned JSON/YAML dataset or typed module** stored directly within the repository (e.g. `data/technology-catalog/`). It requires zero database setup, zero network calls, runs instantly in Docker or local Python, and provides Git-tracked versioning out of the box.

### Finding 5: Micro-Optimization Weeds (Floating-Point Drift)
- **Severity**: 🟢 **Nit**
- **Affected Scope**: Critic Finding 3 (`Float Drift`)
- **Simplicity Rationale**: Warning about cross-platform floating-point drift altering candidate rankings across macOS and Linux is an unnecessary rabbit hole. StackSense scores candidates using discrete integer weights (1–5) and normalized criteria. A simple deterministic tie-breaker (higher score $\to$ lower cost $\to$ alphabetical component ID) guarantees identical cross-platform results with zero custom fixed-point arithmetic crates or math libraries.

---

## 3. Required Updates to `docs/product.md` (Simplest Path to Full Compliance)

To satisfy the official problem statement without bloat or weeds, `docs/product.md` should be updated with the following concise, high-altitude adjustments:

### Finding 6: Anchor Directly to the Official Section 3.1 & Section 4 JSON Contracts
- **Severity**: 🔴 **Blocker**
- **Affected Scope**: `## Inputs to collect` (lines 32–46), `## Outputs` (lines 48–55)
- **Simplicity Guidance**:
  - Replace the open-ended input table with the 8 official schema namespaces: `project.*`, `scale.*`, `team.*`, `budget.*`, `timeline.*`, `infrastructure.*`, `requirements.*`, `compliance`, and `priorities.*`.
  - Prune out-of-scope speculative outputs: remove `"migration notes"` (line 30), `"operational complexity estimate"` (line 52), and `"follow-up questions"` (line 54).
  - Explicitly bind output deliverables to the Section 4 schema: `status` (`ok`, `ok_with_warnings`, `infeasible`, `invalid_input`), `summary`, `architecture_style`, `stack` (4 core layers + `supporting[]`), `estimated_monthly_cost_usd` ({min, max, assumptions[]}), `warnings[]` ({code, severity, message, fields}), `assumptions[]`, and `validation_errors[]`.

### Finding 7: Reclassify Hard vs. Soft Constraints per Section 5.3
- **Severity**: 🟡 **Major**
- **Affected Scope**: `## Product principles` (line 17)
- **Simplicity Guidance**: Line 17 incorrectly bundles budget ceilings and availability into hard constraints.
  - **Hard Constraints**: `data_residency`, `compliance`, `deployment_model`, and explicit `cloud_preference`. Violations can never be produced silently and trigger `status: "infeasible"` or critical warnings.
  - **Soft Constraints**: `budget`, `timeline`, and `priorities`. These guide candidate scoring and trade-offs. If a budget or timeline cannot be met, the engine recommends the closest viable stack with `status: "ok_with_warnings"`, documenting the budget stretch in `warnings[]` and `assumptions[]`.

### Finding 8: Enshrine LLM Boundaries, the LLM-Off Switch, and Zero-Paid-Key Mandate
- **Severity**: 🟡 **Major**
- **Affected Scope**: `## Non-goals for v1` (lines 56–62) & `## Product principles` (lines 16–23)
- **Simplicity Guidance**: The document must explicitly state the competition rules (§2.2 & §5.1):
  - Stack selection logic is 100% deterministic code (rules + scoring).
  - LLM usage is strictly optional and restricted to free-text parsing and explanation wording polish.
  - A mandatory switch (`ENABLE_LLM=false` / `--no-llm`) must guarantee identical recommendation outputs.
  - The engine must be 100% functional locally with zero paid API keys.

### Finding 9: Ground "Catalogue" and "Scenarios" for Fresh Readers
- **Severity**: 🟡 **Major**
- **Affected Scope**: `## Product principles` (line 22), `## Success measures` (lines 64–68)
- **Simplicity Guidance**:
  - Define the "technology catalogue" as a versioned, static curated dataset within the repository containing real, maintained technologies and cited evidence (documentation, pricing, benchmarks).
  - Define "scenarios" as standard JSON scenario files, referencing public benchmarks P1–P6 and automated hidden test suites.

### Finding 10: Replace Hackathon Meta-Commentary with the Official Evaluation Rubric
- **Severity**: 🟢 **Nit**
- **Affected Scope**: `## Success measures` (lines 63–68)
- **Simplicity Guidance**: Reframe subjective contest phrasing into measurable quality gates matching the Section 8 scoring rubric:
  1. **Recommendation Quality (35%)**: Hard constraints strictly respected; appropriate architectures for scale and budget; identical outputs under LLM-off switch.
  2. **Input Design & Research (30%)**: Full Section 3.1 input schema support; robust field-level validation; cited knowledge base.
  3. **Reasoning & Explainability (20%)**: Every choice has an input-linked justification (`driven_by`), $\ge 1$ alternative with `why_not`, and known trade-offs.
  4. **Documentation Quality (15%)**: Flawless local setup from README in under 15 minutes.

---

## 4. Altitude Control Guidelines for Document Refactoring

1. **Keep Architecture at High Altitude**: Summarize the pipeline in 1 concise diagram (`Input Normalization -> Hard Constraint Pruning -> Layer Scoring & Compatibility Filter -> JSON Serialization`). Do not paste class structures, function names, or internal module code.
2. **Keep Alternatives Conceptual**: State *why* a two-phase deterministic rule/scoring hybrid was chosen over pure LLM prompting (fails §5.1 rules) and rigid hardcoded trees (unmaintainable combinatorial paths).
3. **Keep Knowledge Base Storage Simple**: Treat the catalogue as a versioned data file. Do not invent database migration frameworks or external query layers.
4. **Prune Speculative Features**: Do not add feature branches for conversational interviewing, live cloud billing scrapers, or automatic code scaffolding.
