# Stage 9: Implementation Readiness Report

**Target Document**: [`docs/designs/ui-ux-core-enhancements.md`](file:///Users/amankumar/Aman/Hackathon/StackSence-'26/docs/designs/ui-ux-core-enhancements.md#L316-L401)  
**Standard Applied**: [`implementation-readiness-standard.md`](file:///Users/amankumar/.gemini/config/plugins/egm/resources/document_standards/implementation-readiness-standard.md)  
**Reviewers**: `egm-implementation-readiness` (Tech Lead), `egm-codebase-details` (Codebase Auditor), `egm-style` (Style Reviewer)  
**Scope Audited**: DetailedRange (Lines 316–401)  
**Execution Mode**: Uninterrupted Full Flow  
**Date**: 2026-11-13  
**Status**: **REVISION REQUIRED BEFORE CODE EXECUTION**

---

## Executive Summary

The Detailed Implementation Plan in lines 316–401 was drafted prior to the finalization of the [Stage 8 Intermediate Zoom Out Review](file:///Users/amankumar/Aman/Hackathon/StackSence-'26/intermediate_zoom_out_report.md). As a result, it retains the deprecated subsystems (`repair.py`, `models/studio.py`, and `POST /api/studio/recommend`), re-introduces the speculative 5-axis scoring matrix, lacks pure-Python SVG layout specifications, and omits the phased execution structure required by the Implementation Readiness Standard.

To reach execution readiness, the Detailed Implementation Plan must be updated to reflect the converged architecture:
1. Purge `repair.py` and `models/studio.py`; inject actionable relaxation heuristics directly into `engine.py` and `validation.py`.
2. Define defensive guards (`stack is None`) and label sanitization in `topology.py`, with pure-Python SVG generation.
3. Establish `POST /api/topology` and startup memoization for `GET /api/scenarios/matrix` in `web.py`, with local static asset vendoring.
4. Structure implementation into 5 sequential, testable phases.

---

## Consolidated Findings

### 🔴 Blockers

#### 1. Re-Introduction of Deprecated Subsystems (`repair.py` & `models/studio.py`)
* **Reviewers**: `egm-implementation-readiness` (Finding 1), `egm-codebase-details` (Finding 1)
* **Affected Scope**: Lines 320–328, 341–350, 355
* **Discrepancy**: Stage 8 eliminated `repair.py` and `models/studio.py` to prevent architectural split-brain and preserve the canonical Section 4 `ScenarioOutput` contract. Lines 320–328 and 341–350 re-propose creating these exact files, while omitting `engine.py` and `validation.py` from target modifications.
* **Actionable Fix**:
  - Remove `src/stacksense/models/studio.py` and `src/stacksense/repair.py` from the target file list.
  - Add `src/stacksense/engine.py` and `src/stacksense/validation.py` to target modifications.
  - Integrate actionable relaxation guidance directly into `WarningItem.message` (e.g., minimum budget delta and low-cost architectural alternatives) and `assumptions[]`.
  - Retain `POST /api/recommend` as the single canonical recommendation API.

#### 2. Re-Introduction of Speculative 5-Axis Scoring Matrix
* **Reviewers**: `egm-implementation-readiness` (Finding 2), `egm-codebase-details` (Finding 1)
* **Affected Scope**: Lines 324, 326, 363
* **Discrepancy**: The plan still includes `TradeoffScoreItem` and arbitrary 1–5 numerical scoring, which violates YAGNI and lacks data grounding in `catalogue.json`.
* **Actionable Fix**: Delete `TradeoffScoreItem` and `tradeoff_scores`. Tab 3 will render an Architectural Trade-Off Matrix grounded in verified Section 4 data: chosen component vs. rejected alternatives, input-traceable `driven_by` fields, comparative `why_not` rationales, and documented `tradeoffs`.

#### 3. Missing Pure-Python SVG Generator Specification & Defensive Handling
* **Reviewers**: `egm-implementation-readiness` (Finding 3), `egm-codebase-details` (Finding 2)
* **Affected Scope**: Lines 329–340
* **Discrepancy**:
  - The plan only mentions `generate_topology_mermaid`; `generate_topology_svg` is completely omitted without dimensions, coordinates, or layout details.
  - No defensive handling is specified for `output.stack is None` (infeasible scenarios like EC-01) or `"None"` layers (static sites like P1/EC-04), which will cause `AttributeError`.
  - No node label sanitization helper is specified to escape quotes and brackets.
* **Actionable Fix**:
  - Define function signatures in `src/stacksense/topology.py`:
    ```python
    def generate_topology_mermaid(output: ScenarioOutput, scenario_input: Optional[dict[str, Any]] = None) -> str: ...
    def generate_topology_svg(output: ScenarioOutput, scenario_input: Optional[dict[str, Any]] = None) -> str: ...
    def sanitize_node_label(label: str) -> str: ...
    ```
  - Define SVG specifications: root `<svg viewBox="0 0 800 600">`, 5 vertical tier bands (Clients, Edge, Compute, Persistence, Async), dark-theme styling, and connecting path markers.
  - Implement defensive guards: return a diagnostic conflict node if `output.stack is None` or `output.status in ("infeasible", "invalid_input")`; omit `"None"` layers cleanly.

#### 4. Visualization Boundary Violation & Missing Offline Asset Vendoring
* **Reviewers**: `egm-implementation-readiness` (Finding 4), `egm-codebase-details` (Finding 1)
* **Affected Scope**: Lines 354–356
* **Discrepancy**: Siphons visualization into `POST /api/studio/recommend` instead of providing a dedicated auxiliary endpoint, and omits local static asset vendoring for offline evaluation.
* **Actionable Fix**:
  - Replace `POST /api/studio/recommend` with a lightweight endpoint:
    `POST /api/topology`: Accepts `{ "output": ScenarioOutput, "scenario_input": dict }` and returns `{ "mermaid": str, "svg": str }`.
  - Add local vendor directory `src/stacksense/static/vendor/` and mount it via FastAPI `StaticFiles`.

---

### 🟡 Major Findings

#### 5. Omission of Phased Implementation Structure
* **Reviewer**: `egm-implementation-readiness` (Finding 5)
* **Affected Scope**: Lines 316–401
* **Discrepancy**: Presents a flat list of files without incremental, testable phases.
* **Actionable Fix**: Structure implementation into 5 sequential phases:
  - **Phase 1: Core Topology Engine & Sanitization** (`topology.py`, `tests/test_topology.py`).
  - **Phase 2: Core Engine Relaxation Guidance** (`engine.py`, `validation.py`, `tests/test_edge_cases.py`).
  - **Phase 3: Web Visualization Endpoints & Memoization** (`POST /api/topology`, `GET /api/scenarios/matrix` in `web.py`).
  - **Phase 4: Dashboard UI & Static Vendoring Overhaul** (`static/`, HTML tabs in `web.py`).
  - **Phase 5: Documentation & Packaging Validation** (`docs/project-report.md`, `./scripts/package_submission.sh`).

#### 6. Underspecified Matrix Startup Memoization
* **Reviewers**: `egm-implementation-readiness` (Finding 6), `egm-codebase-details` (Finding 5)
* **Affected Scope**: Line 356
* **Discrepancy**: Fails to specify how benchmark scenarios are memoized at startup.
* **Actionable Fix**: Define `_BENCHMARK_MATRIX_CACHE` populated on server startup via lifespan handler, serving `GET /api/scenarios/matrix` in <2ms.

#### 7. Uncalibrated Promotional Claims in Rationales
* **Reviewer**: `egm-style` (Findings 1, 2, 3)
* **Affected Scope**: Lines 349, 368, 377
* **Discrepancy**: Meta-rubric leakage ("Directly boosts the Recommendation Quality (35%) score") and uncalibrated claims ("Guarantees test coverage").
* **Actionable Fix**: Replace with objective engineering descriptions of what the code validates.

---

### 🟢 Nits

8. **Test Suite Organization**: Split tests into `tests/test_topology.py` (pure Python SVG/Mermaid) and `tests/test_web_studio.py` (FastAPI routes).
9. **Defensive Cost Guarding**: Guard all cost comparisons with `if output.estimated_monthly_cost_usd is not None:`.
10. **Availability Type Parsing**: Parse string enum availability values safely before comparison.
