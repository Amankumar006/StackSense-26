# Official-Contract Reconciliation — StackSense

**Status:** Completed  
**Release Checkpoint:** 10 November 2026, 10:00 AM IST  
**Reconciliation Date:** 11 November 2026  
**Source Document:** [Synergy '26 Problem Statement (PDF v1.0)](official-problem-statement.pdf)  
**Authority:** The official Unstop problem statement, I/O specification, sample scenarios, report template, and folder structure supersede every draft in this repository.

---

## 1. Release Extraction & Decision Sheet

| Contract Area | Official Requirement | Local Impact | Decision | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Required inputs** | 8 structured namespaces (Section 3.1): `project`, `scale`, `team`, `budget`, `timeline`, `infrastructure`, `requirements`, `compliance`, `priorities`. | Replaced informal dictionary in `docs/input-schema.md`. | **Adopt** | Completed |
| **Input format / validation** | Strict JSON schema; field-level validation errors reported under `validation_errors[]` with `status: "invalid_input"`. | Domain models in `src/stacksense/models/`. | **Adopt** | Models designed |
| **Required outputs** | `status`, `summary`, `architecture_style`, `stack` (4 core layers + `supporting[]`), `estimated_monthly_cost_usd`, `warnings[]`, `assumptions[]`, `validation_errors[]`. | Output contract in `docs/design.md`. | **Adopt** | Completed |
| **Mandatory stack categories** | Core: `frontend`, `backend`, `database`, `hosting`. Supporting: `cache`, `queue`, `search`, `auth`, `storage`, `cdn`, `realtime`, `payments`, `ml`, `ci_cd`, `observability`, `other`. | Catalogue schema and composer rules. | **Adopt** | Completed |
| **Permitted / prohibited tools** | Decision must be custom logic (rules, scoring, CSP). LLMs permitted ONLY for description parsing and explanation polish. Mandatory LLM-off switch. No paid keys required. | Engine architecture; `--no-llm` flag. | **Adopt** | Enforced |
| **Public sample scenarios** | 6 scenarios: P1 (Portfolio/Blog), P2 (Marketplace), P3 (Realtime Collab), P4 (Digital Lending), P5 (Internal HR), P6 (Offline-first Survey). | Saved to `data/scenarios/` and `tests/fixtures/`. | **Adopt** | Completed |
| **Hidden test implications** | Edge cases: missing fields, invalid types/ranges, contradictions, over-engineering traps, regulatory, existing systems, restricted deployment, skill mismatch, deprecated tech. | Validation engine & edge-case test suite. | **Adopt** | Planned |
| **Report template requirements** | Strictly $\le 15$ pages, 10 sections + title page + AI assistance declaration. Real screenshots. | `docs/project-report.md`. | **Adopt** | Aligned |
| **Drive-folder structure** | `StackSense26_<FullName>/` with `source/`, `outputs/` (P1_output.json..P6_output.json), `Report_<FullName>.pdf`. | Packaging runbook & checklist. | **Adopt** | Aligned |
| **Evaluation rubric** | Recommendation Quality (35%), Input Design & Research (30%), Reasoning & Explainability (20%), Documentation Quality (15%). | Prioritization and test strategy. | **Adopt** | Aligned |

---

## 2. Draft-to-Contract Mapping Review

| Existing Artifact | Planned Treatment | Action Taken |
| :--- | :--- | :--- |
| `docs/product.md` | Align with Section 3.1 & Section 4 JSON contracts, strip speculative conversational interviewing and out-of-scope outputs. | **Refactored** to full compliance per Stage 8 review. |
| `docs/input-schema.md` | Retype and align with Section 3.1 namespaces, types, and enums. | **Refactored** to exact official schema. |
| `docs/design.md` | Update output schema to Section 4 format; implement hard constraint filter and multi-objective scoring. | **Ready for alignment** in Phase 2. |
| `data/scenarios/` | Ingest public scenarios P1 through P6. | **Extracted and verified** (`P1.json` – `P6.json`). |
| `docs/submission-checklist.md` | Adopt `StackSense26_<FullName>/` folder layout and deadline (15 Nov 2026, 23:59 IST). | **Updated**. |

---

## 3. Go / No-Go Gates Check

- [x] We know whether the required interface is UI, API, CLI, files, or another format (**CLI scenario runner + lightweight UI form**).
- [x] We know the exact required input and output representation (**Section 3.1 and Section 4 JSON schemas**).
- [x] We know whether catalogue data, external APIs, or model usage has restrictions (**Decision logic must be our own; LLM-off switch mandatory; zero paid keys required**).
- [x] We know the public scenarios and the likely dimensions hidden tests will vary (**P1–P6 public benchmarks + 9 edge case categories**).
- [x] We know the mandatory report structure and final Drive-folder layout (**10-section report $\le 15$ pages, `StackSense26_<FullName>/` structure**).
- [x] Any pre-release draft that conflicts with the release has been marked retired or adapted.

**VERDICT: GO FOR IMPLEMENTATION.**
