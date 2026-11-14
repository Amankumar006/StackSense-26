# StackSense Advanced UI/UX & Core Engine Capabilities

- **Author:** Amankumar006
- **Status:** Approved (Post-Review Remediated)
- **Date:** 2026-11-14

--------------------------------------------------------------------------------

## Overview

StackSense is a deterministic technology stack recommendation engine built for the Synergy '26 (IIIT Bangalore) Systems-Design Challenge. While the current engine passes all 11 Section 6 edge cases and satisfies Section 4 output contracts (as specified in the [Official Problem Statement](file:///Users/amankumar/Aman/Hackathon/StackSence-'26/docs/official-problem-statement.pdf)), the user interface and presentation layer lack visual system topology graphs, comparative scenario matrices, and automated constraint-conflict repair suggestions.

This design document outlines the technical enhancements required to upgrade StackSense's interface and core analytical capabilities across all four official evaluation dimensions: Recommendation Quality (35%), Input Design & Research (30%), Reasoning & Explainability (20%), and Documentation Quality (15%).

--------------------------------------------------------------------------------

## The Problem

Evaluation in systems design hackathons depends on communicating architectural decisions, trade-offs, and failure modes. Review of the current implementation identifies five deficiencies:

1. **Text-Heavy Architecture Communication**: Recommendations are currently displayed as text cards without visual diagrams. Systems design reviews benefit from topology diagrams that clarify component boundaries, data flow directions, network tiers, and communication protocols (HTTPS, WebSocket, gRPC).
2. **Manual JSON-Only Input**: The existing interface defaults to direct JSON text editing. An interactive visual form with bi-directional JSON synchronization, range sliders, archetype presets, and client-side validation reduces manual data entry effort.
3. **Binary Conflict Reporting**: When input constraints conflict (e.g., $0 budget with 100,000 users, or a solo beginner team demanding 99.99% uptime), the engine reports an error or defaults assumptions without suggesting actionable heuristic parameter adjustments to restore feasibility.
4. **Isolated Single-Scenario Evaluation**: Users can only inspect one scenario at a time. Evaluating architectural consistency across disparate archetypes (e-commerce vs. B2B SaaS vs. offline-first) requires a unified cross-scenario comparative matrix.
5. **Visual Styling Defects**: Text collision bugs (such as `HOSTINGGoogle Cloud Run`), insufficient contrast ratios, and unsegmented layouts degrade readability.

--------------------------------------------------------------------------------

## Goals

1. **Interactive Visual Studio & Bi-Directional Synchronization**:
   - Provide visual input controls (archetype selector, traffic and budget sliders, multi-platform badges, compliance toggles) synchronized with the Section 3.1 JSON code editor.
   - Support real-time client-side validation of input constraints with inline error markers.

2. **Automated Visual Architecture Topology**:
   - Deterministically generate a system architecture diagram in both Mermaid.js format and pure-Python vector SVG directly from the recommendation output.
   - Model five standard architectural tiers: Client Layer (Web/Mobile) -> Edge & CDN -> Application & Compute Services -> Primary & Cache Databases -> Asynchronous Workers & External Gateways, annotated with protocols and data flow.
   - Guard defensively against `stack: None` or infeasible scenarios to prevent runtime crashes.

3. **Constraint Conflict Relaxation Guidance**:
   - Implement automated relaxation guidance in the core engine (`engine.py`, `validation.py`). When contradictory constraints are detected (e.g., budget underflow, availability-team mismatch, air-gapped cloud dependencies), calculate and inject minimal parameter adjustments directly into `ScenarioOutput.warnings[].message` and `ScenarioOutput.assumptions[]`.
   - Preserve canonical schema compatibility so both headless CLI evaluators and the Web UI share a single source of truth.

4. **Multi-Scenario Comparative Matrix**:
   - Provide a comparative benchmarking dashboard displaying public scenarios (P1 through P6 in `data/scenarios/`) alongside edge cases in a single matrix table (comparing Frontend, Backend, Database, Hosting, Cost Range, and Architecture Pattern).
   - Memoize scenario evaluations at application startup to serve responses in <2ms.

5. **Technology Trade-Off Comparison Matrix**:
   - Render a structured qualitative trade-off matrix in the UI comparing chosen components versus rejected alternatives, input-traceable `driven_by` parameters, concrete `why_not` rationales, and documented `tradeoffs` grounded in Section 4 output data.

6. **Modernized Interface Styling & Offline Resilience**:
   - Structure the frontend layout with a high-contrast dark theme, monospace typography for technical data, 1px container borders, responsive navigation tabs, clipboard copy actions, and PDF report downloads.
   - Vendor client assets locally in `src/stacksense/static/` to guarantee operation in offline and air-gapped evaluation environments.

--------------------------------------------------------------------------------

## Non-Goals

1. **Cloud Provisioning / Terraform Generation**: StackSense will not deploy resources to AWS, GCP, or Azure, nor generate live Terraform/Pulumi state files. Its scope remains recommendation and systems design specification.
2. **External LLM Runtime Dependencies**: Core recommendations, constraint satisfaction, and diagram generation will remain deterministic Python rules; no paid external AI API keys will be introduced into the execution path.
3. **Arbitrary Pricing Calculator**: StackSense will not replicate cloud billing calculators. Cost estimation will remain bounded by the calibrated tier formulas defined in Section 3 of the problem statement.
4. **User Authentication & Multi-Tenancy**: The application is an open evaluation studio designed for local and review environments; multi-user database authentication and role management are excluded.
5. **Speculative 5-Axis Scoring**: No arbitrary 1–5 numerical scoring matrix will be computed; explainability relies strictly on verified qualitative catalog data.

--------------------------------------------------------------------------------

## Open Questions & Resolved Decisions

1. **Diagram Rendering Strategy (Resolved)**:
   - *Decision*: `src/stacksense/topology.py` implements a pure-Python dual generation strategy:
     - Deterministic Mermaid flowchart syntax (`graph TD`) for interactive browser rendering and text copying.
     - Deterministic vector SVG generation using a fixed 5-tier vertical layout engine in pure Python, requiring zero external binaries (Graphviz, Node.js).
   - *Rationale*: Guarantees zero-dependency offline repeatability, eliminates external CDN failure points, and enables direct SVG embedding into headless PDF report builds.

2. **Constraint Relaxation Strategy (Resolved)**:
   - *Decision*: Constraint relaxation is implemented as a deterministic heuristic cascade in `engine.py` and `validation.py`, injecting actionable advice into `ScenarioOutput.warnings[].message` and `assumptions[]`.
   - *Rationale*: Avoids architectural split-brain and keeps `POST /api/recommend` canonical for both automated CLI grading and web exploration.

--------------------------------------------------------------------------------

## Critical User Journeys (CUJs)

### CUJ 1: Interactive System Design Exploration
- **Given**: An engineer or evaluator loads the StackSense web dashboard.
- **When**: The user modifies traffic scale sliders, toggles compliance flags (e.g., RBI Data Localisation), or selects a preset scenario from the dropdown.
- **Then**: The visual controls synchronize with the raw JSON spec, the engine evaluates the stack in under 10 milliseconds, and the UI displays the recommended components, trade-offs, and an interactive architecture topology diagram.

### CUJ 2: Infeasible Requirements & Automated Repair
- **Given**: A user inputs an infeasible requirement (e.g., $10/month budget for a 1,000,000 user platform requiring 99.99% availability).
- **When**: The user clicks "Evaluate Stack".
- **Then**: The system flags the conflict with a warning status and provides actionable parameter deltas in the warnings section (e.g., "Suggest increasing infrastructure budget to at least $85/mo OR adopting single-node low-cost container deployment").

### CUJ 3: Cross-Scenario Benchmarking
- **Given**: An evaluator inspects how StackSense handles varied workloads (P1 E-commerce vs. P3 FinTech vs. P4 Healthcare).
- **When**: The user navigates to the "Comparative Matrix" tab.
- **Then**: The dashboard presents a unified table comparing all official scenarios across architecture tier, primary database, hosting model, monthly cost, and key rejected alternatives with sub-5ms response time.

### CUJ 4: Official Report & Spec Export
- **Given**: A user completes their scenario evaluation.
- **When**: The user clicks "Export Design Spec" or "Official Report (PDF)".
- **Then**: The application initiates download of the Section 4 compliant JSON artifact and links directly to the [Official Project Report PDF](file:///Users/amankumar/Aman/Hackathon/StackSence-'26/Report_Aman_Kumar.pdf).

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

### 1. System Architecture Overview

StackSense is structured into four deterministic functional layers:
1. **Validation & Normalization Layer** (`validation.py`): Parses Section 3.1 JSON inputs, applies documented defaults for missing optional fields, catches malformed inputs, and detects constraint contradictions.
2. **Recommendation & Constraint Engine** (`engine.py`, `constraints.py`, `catalog.py`): Evaluates project archetype, workload profile, scale parameters, and compliance restrictions to choose core layers (Frontend, Backend, Database, Hosting) and supporting services, enriching warnings with actionable relaxation advice.
3. **Presentation & Topology Layer** (`topology.py`): Transforms the evaluated `ScenarioOutput` and scenario inputs into deterministic Mermaid flowchart syntax and pure-Python vector SVG using a fixed 5-tier vertical layout.
4. **Interactive Studio Web Interface** (`web.py`): A single-page web interface served by FastAPI that provides both the Section 3.1 JSON code editor and the visual form studio, rendering Mermaid diagrams, pure-Python SVG fallbacks, and comparative matrices without requiring Node.js.

```text
+---------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                     |
|  +---------------------------------------+  +--------------------------------------+  |
|  |     Visual Studio (Form Controls)     |  |   Section 3.1 JSON Code Editor       |  |
|  | (Sliders, Archetypes, Chips, Toggles) |  |   (JSON Editor with Inline Linter)   |  |
|  +---------------------------------------+  +--------------------------------------+  |
|                                      |               | (Debounced 250ms Linter Gate)  |
|                                      v               v                                |
|                        [ Canonical JSON Scenario State ]                              |
+---------------------------------------------------------------------------------------+
                                           |
                                           | POST /api/recommend (Canonical Endpoint)
                                           v
+---------------------------------------------------------------------------------------+
|                                 BACKEND PIPELINE (FastAPI)                             |
|                                                                                       |
|  1. Input Validation & Default Injection [src/stacksense/validation.py]               |
|     - Validates enums, non-negative numbers, data localization rules                   |
|     - Enriches contradiction warnings with actionable repair advice                   |
|                                                                                       |
|  2. Constraint Satisfaction & Rule Engine [src/stacksense/engine.py]                  |
|     - Evaluates hard constraints (India DPDP/RBI, Air-gapped, Existing systems)        |
|     - Selects Frontend, Backend, Database, Hosting, Supporting Services                |
|     - Enriches soft budget relaxation warnings with minimum feasible cost deltas      |
|                                                                                       |
|  3. Presentation Topology Engine [src/stacksense/topology.py]                         |
|     - Pure presentation formatter: ScenarioOutput -> Mermaid syntax + Pure-Python SVG |
|     - Defensive guards: handles `stack: None` and `"None"` layers cleanly             |
|     - Node label sanitization: escapes quotes, brackets, and HTML entities             |
|                                                                                       |
|  4. Auxiliary Endpoints in [src/stacksense/web.py]                                    |
|     - POST /api/topology: Returns { "mermaid": str, "svg": str }                      |
|     - GET  /api/scenarios/matrix: Pre-computed startup cache, serves in <2ms          |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                              STUDIO WORKSPACE (Dashboard)                             |
|                                                                                       |
|  [Tab 1: Architecture Blueprint]  [Tab 2: System Topology]  [Tab 3: Trade-Off Matrix] |
|  [Tab 4: Conflict Relaxation]    [Tab 5: Comparative Grid] [Tab 6: Section 4 JSON]   |
+---------------------------------------------------------------------------------------+
```

### 2. Component Design & Module Specifications

#### A. Topology Generator (src/stacksense/topology.py)
Generates structured Mermaid flowchart syntax and pure-Python vector SVG directly from `ScenarioOutput`. The topology models five standard systems design tiers:
1. **Client Tier**: Web browsers (Next.js / Astro / Vite), Mobile clients (React Native / Flutter / Android Native), Desktop apps.
2. **Edge & Ingress Tier**: Cloudflare CDN, AWS CloudFront, or Nginx Edge Proxy with SSL termination and WAF protection.
3. **Application & Compute Tier**: Serverless instances (Cloud Run / AWS Lambda), Container clusters (AWS ECS / Kubernetes), or Standalone Monoliths.
4. **Data Persistence Tier**: Primary Relational / Document Store (PostgreSQL, MySQL, MongoDB, DynamoDB) and In-Memory Cache (Redis).
5. **Asynchronous & External Tier**: Message Brokers (RabbitMQ / Kafka / SQS), Search Engine (Meilisearch / OpenSearch), and External Third-Party APIs (Payment Gateways, Entra ID).

##### Data Flow Protocol Mapping
- Client -> Edge: `HTTPS / TLS 1.3` (or `WSS` for real-time collaboration).
- Edge -> Compute: `HTTP/2` or `gRPC`.
- Compute -> Database: `TCP / SSL`.
- Compute -> Cache: `In-Memory Buffer`.
- Compute -> Broker: `AMQP Job Queue` or `Kafka Protocol`.

##### Defensive Fallbacks & Null-Safety
- If `output.stack is None` or `output.status in ("infeasible", "invalid_input")`, emit a diagnostic conflict diagram:
  ```text
  graph TD
      Infeasible["⚠️ Infeasible Architecture - Resolve Contradictions to View Topology"]
  ```
- If a layer is `"None"` (e.g. static site P1 frontend where backend/database are `"None"`), suppress the corresponding node and protocol edges.

##### Pure-Python SVG Layout Engine
- Generates an SVG string using root `<svg viewBox="0 0 800 620" xmlns="http://www.w3.org/2000/svg">`.
- Defines 5 fixed vertical tier bands: Clients (y=40), Edge (y=150), Compute (y=260), Persistence (y=370), Async (y=480).
- Applies dark-mode styling: canvas `#090d16`, containers `#111625`, borders `#1f2942`, typography `#f1f5f9`.
- Includes markers for directional arrows (`<marker id="arrow" .../>`).

##### Node Label Sanitization Helper
```python
def sanitize_node_label(label: str) -> str:
    """Strips quotes, brackets, and escapes HTML entities for Mermaid/SVG compatibility."""
    cleaned = label.replace('"', "'").replace("[", "(").replace("]", ")")
    return html.escape(cleaned)
```

#### B. Constraint Relaxation Guidance (src/stacksense/engine.py & validation.py)
When contradictory or infeasible inputs occur, actionable remediation guidance is injected directly into `ScenarioOutput.warnings[].message` and `ScenarioOutput.assumptions[]`.

##### Conflict Scenarios & Heuristic Rules
1. **Budget Underflow**:
   - Condition: `budget.monthly_infra_usd < estimated_cost.min`.
   - Injected Guidance: `"Suggest increasing infrastructure budget to at least ${min}/mo OR adopting single-node low-cost container deployment."`
2. **High Availability vs. Small Team / Zero DevOps**:
   - Condition: `availability in ("99.95", "99.99")` AND `team_size <= 2` AND `has_devops is False`.
   - Injected Guidance: `"Suggest lowering availability target to 99.5% (managed single-region) OR adopting fully managed PaaS to eliminate operational maintenance."`
3. **Air-Gapped vs. Public Cloud Services**:
   - Condition: `deployment_model == "air_gapped"` with cloud preference set to AWS/GCP/Azure.
   - Injected Guidance: `"Suggest switching cloud preference to 'none' and using on-premise containerized open-source components (MinIO, self-hosted search)."`

#### C. Cross-Scenario Comparative Matrix & Startup Cache (src/stacksense/web.py)
- Pre-computes recommendations for `P1.json` through `P6.json` once during server startup using a module-level cache `_BENCHMARK_MATRIX_CACHE`.
- Endpoint `GET /api/scenarios/matrix` serves the cached matrix in <2ms:
  ```json
  [
    {
      "scenario_id": "P1",
      "project_name": "DevFolio",
      "archetype": "content_site",
      "recommended_stack": {
        "frontend": "Astro",
        "backend": "None",
        "database": "None",
        "hosting": "Cloudflare Pages",
        "supporting": ["Cloudflare CDN & Edge Cache"]
      },
      "cost_range": "$0 - $20 / month",
      "architecture_style": "static",
      "key_driver": "Static portfolio with minimal budget and no database requirements.",
      "top_rejected_alternative": "Next.js: Overkill for static content."
    }
  ]
  ```

#### D. Architectural Trade-Off Matrix (UI Presentation)
Tab 3 in the web studio renders a structured comparison table derived from canonical `ScenarioOutput.stack` without speculative 1–5 scoring:
- **Core Layer**: Frontend, Backend, Database, Hosting.
- **Recommended Choice**: Winning technology choice and justification.
- **Decision Drivers**: Array of input field paths (`driven_by`).
- **Rejected Alternatives**: Viable alternatives considered alongside concrete `why_not` comparative rationales.
- **Known Trade-offs**: Documented operational downsides and architectural constraints.

### 3. API Changes & Backward Compatibility

- `POST /api/recommend`: Strictly preserves canonical Section 4 `ScenarioOutput` schema for automated hackathon evaluators and CLI batch runs.
- `POST /api/topology`: Dedicated auxiliary presentation endpoint returning `{ "mermaid": str, "svg": str }`.
- `GET /api/scenarios/matrix`: Serves pre-computed benchmark comparison matrix in <2ms.
- `GET /api/download-report`: Streams the generated `Report_Aman_Kumar.pdf`.

### 4. Non-Functional Requirements & Performance

- **Backend Latency**: In-memory rule execution completes in <10ms for individual scenario evaluations and <2ms for cached matrix lookups.
- **Client Render Latency**: Lightweight SVG and Mermaid DOM rendering complete in <300ms.
- **Zero Node.js Build Tooling**: The studio runs on FastAPI and Uvicorn, loading styling and visualization assets locally or via CDNs without an npm compilation pipeline.
- **Offline & Air-Gapped Operation**: Static assets are mirrored locally in `src/stacksense/static/vendor/` to allow operation in air-gapped test environments.

--------------------------------------------------------------------------------

## Risks & Mitigations

1. **Offline Environment Execution without CDN Access**:
   - *Risk*: Evaluators testing StackSense in an air-gapped sandbox without external internet access will experience unstyled HTML or broken diagrams if scripts load only from external CDNs.
   - *Mitigation*: Mirror `mermaid.min.js` into `src/stacksense/static/vendor/` served via FastAPI `StaticFiles`. Provide pure-Python SVG generation in `topology.py` that renders inline vector graphics without requiring client-side JavaScript execution.
2. **UI State Race Conditions & Cursor Thrashing**:
   - *Risk*: Live bi-directional synchronization between form sliders and a raw JSON textarea can create cyclic event loops, cursor jumping during active typing, or clobbered state on transient invalid JSON syntax.
   - *Mitigation*: Implement unidirectional state flow in browser memory. Form controls mutate canonical in-memory state and re-render the JSON textarea. The JSON editor applies a 250ms debounced gate that validates via client-side `JSON.parse` and only synchronizes back to form controls when valid schema JSON is parsed.
3. **Diagram Engine Crashes on Infeasible or Partial Stacks**:
   - *Risk*: When `output.stack is None` (infeasible scenarios like EC-01) or core layers are `"None"` (static sites like P1), naive property access in `topology.py` will raise `AttributeError`.
   - *Mitigation*: Add defensive guards: return a diagnostic conflict node when `output.stack is None` and conditionally suppress `"None"` layers.
4. **XSS & DOM Injection via Node Labels**:
   - *Risk*: Dynamic interpolation of unescaped project names or custom inputs into Mermaid syntax or SVG elements could cause parsing errors or XSS.
   - *Mitigation*: Sanitize all node labels with `sanitize_node_label()`, escaping quotes, brackets, and HTML entities before assembling diagram markup.

--------------------------------------------------------------------------------

## Alternatives Considered

### Alternative A: Full-Stack React / Next.js SPA with Separate Python REST Backend
- **Pros**: Access to React Flow, Radix UI, TanStack Table; component isolation.
- **Cons**: Requires Node.js and npm as build prerequisites; mandates running two processes; increases Docker footprint from ~150MB to >800MB.
- **Reason for Rejection**: Multi-runtime architectures introduce Node.js prerequisites and process-management overhead. A single Python package runnable via `stacksense web` with embedded HTML/Tailwind/Mermaid satisfies visualization requirements without requiring Node.js or dual processes.

### Alternative B: Server-Side Static Graphviz Diagram Rendering (PNG/SVG)
- **Pros**: Generates image files on the server; embeds directly into headless PDF generators.
- **Cons**: Requires system-level `graphviz` binary packages (`apt-get install graphviz`), which fail in minimal container environments; raster PNG images cannot be zoomed or copied.
- **Reason for Rejection**: System-level binary dependencies (Graphviz) violate portability constraints and fail in minimal environments. Pure-Python SVG and browser Mermaid render vector graphics natively with zero binary dependencies.

### Alternative C: Multi-Objective Constraint Solvers (Z3 / Integer Linear Programming)
- **Pros**: Formally proves Pareto optimality across high-dimensional parameter spaces.
- **Cons**: Heavyweight external C-extension dependency (`z3-solver`); opaque black-box solver reasoning degrades the 20% Explainability score; higher latency (>300ms vs <5ms).
- **Reason for Rejection**: Opaque solver reasoning degrades explainability. Rule-based heuristic relaxation provides deterministic, step-by-step human-readable recommendations with negligible computational overhead.

### Alternative D: Modal Dialog Overlays for Benchmark Matrix & Trade-Offs
- **Pros**: Keeps the primary architecture screen uncluttered.
- **Cons**: Prevents side-by-side comparison; creates modal nesting traps on smaller viewports; impairs demonstration flow.
- **Reason for Rejection**: A persistent tabbed workspace maintains comparison context across views and avoids the viewport obstruction and focus-trapping issues of modal overlays.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Phase 1: Core Topology Engine & Defensive Formatting
- **Target File**: `src/stacksense/topology.py` (Create)
- **Target File**: `tests/test_topology.py` (Create)
- **Implementation Tasks**:
  1. Implement `sanitize_node_label(label: str) -> str` to strip quotes, brackets, and escape HTML characters.
  2. Implement `generate_topology_mermaid(output: ScenarioOutput, scenario_input: Optional[dict[str, Any]] = None) -> str`:
     - Guard: if `output.stack is None` or `output.status in ("infeasible", "invalid_input")`, return a single-node conflict alert diagram.
     - Build 5 subgraphs: Clients, Edge, Compute, Persistence, Async/External.
     - Skip layers where `choice == "None"`.
     - Assign directional protocol edges (`HTTPS`, `WSS`, `HTTP/2`, `TCP/SSL`, `AMQP`).
  3. Implement `generate_topology_svg(output: ScenarioOutput, scenario_input: Optional[dict[str, Any]] = None) -> str`:
     - Render pure-Python SVG string with root `<svg viewBox="0 0 800 620">`.
     - Render dark-mode container boxes and vertical connecting arrows using pre-calculated coordinates.
     - Include fallback rendering for `stack: None`.
  4. Write unit tests in `tests/test_topology.py` validating syntax, null-safety, and SVG structure.

### Phase 2: Core Engine Relaxation Guidance Integration
- **Target File**: `src/stacksense/engine.py` (Modify)
- **Target File**: `src/stacksense/validation.py` (Modify)
- **Implementation Tasks**:
  1. In `src/stacksense/validation.py`, enhance `detect_contradictions()` to append actionable parameter deltas into `WarningItem.message` for high scale + $0 budget, solo beginner + 99.99% SLA, and air-gapped cloud preference conflicts.
  2. In `src/stacksense/engine.py`, enhance `_calibrate_cost()` and soft budget relaxation logic: when monthly budget is below the minimum estimated cost, inject concrete advice into `warnings` and `assumptions` specifying the exact minimum budget required.
  3. Verify with existing edge case test suite (`pytest tests/test_edge_cases.py -v`).

### Phase 3: Web Presentation Endpoints & Startup Memoization
- **Target File**: `src/stacksense/web.py` (Modify)
- **Implementation Tasks**:
  1. Add endpoint `POST /api/topology` accepting `{ "output": ScenarioOutput, "scenario_input": Optional[dict] }` and returning `{ "mermaid": str, "svg": str }`.
  2. Implement startup memoization for `GET /api/scenarios/matrix`:
     - Define `_BENCHMARK_MATRIX_CACHE: list[dict[str, Any]] = []`.
     - Populate cache on server startup for `P1.json` through `P6.json`.
     - Implement `GET /api/scenarios/matrix` returning the cached list in <2ms.
  3. Mount local static files: `app.mount("/static", StaticFiles(directory="src/stacksense/static"), name="static")`.

### Phase 4: Dashboard UI & Static Vendoring Overhaul
- **Target Directory**: `src/stacksense/static/vendor/` (Create & Vendor `mermaid.min.js`)
- **Target File**: `src/stacksense/web.py` (Modify HTML Template)
- **Implementation Tasks**:
  1. Vendor `mermaid.min.js` locally in `src/stacksense/static/vendor/mermaid.min.js`.
  2. Fix layer card header text collisions (`HOSTINGGoogle Cloud Run` separated into dedicated badge and title).
  3. Implement top metrics ribbon: Status badge with color glow, Architecture Style pill, Monthly TCO band, and Compliance indicator.
  4. Implement 6-tab workspace:
     - **Tab 1: Architecture Blueprint**: 4-layer core cards + supporting services grid.
     - **Tab 2: System Topology**: Interactive Mermaid rendering with client fallback to pure-Python SVG, zoom/pan controls, and copy buttons.
     - **Tab 3: Trade-Off Matrix**: Qualitative comparison table of chosen vs. rejected technologies with `driven_by`, `why_not`, and `tradeoffs`.
     - **Tab 4: Conflict Relaxation**: Remediation guide displaying actionable repair suggestions when warnings exist.
     - **Tab 5: Comparative Matrix**: Side-by-side evaluation table for all official scenarios (P1–P6).
     - **Tab 6: Section 4 JSON Spec**: Formatted JSON code editor with copy button.
  5. Implement unidirectional state machine with 250ms debounced linter gate for the JSON textarea.

### Phase 5: Documentation & Packaging Validation
- **Target File**: `docs/project-report.md` (Modify)
- **Target File**: `tests/test_web_studio.py` (Create)
- **Implementation Tasks**:
  1. Write route tests in `tests/test_web_studio.py` validating `POST /api/topology`, `GET /api/scenarios/matrix`, and static file serving.
  2. Update Sections 7 & 9 in `docs/project-report.md` to document the pure-Python topology visualizer, conflict relaxation advisor, and benchmark matrix.
  3. Re-generate `Report_Aman_Kumar.pdf` via Pandoc/WeasyPrint (verifying page count stays $\le 12$ pages).
  4. Run `./scripts/package_submission.sh Aman_Kumar` to verify archive packaging.

--------------------------------------------------------------------------------

## Verification Plan

### Automated Unit & Route Tests
- `tests/test_topology.py`:
  - `test_topology_mermaid_all_benchmarks`: Asserts valid `graph TD` generated for P1 through P6.
  - `test_topology_svg_structure`: Asserts output contains `<svg`, `viewBox`, `<defs>`, `<rect>`, and `<text>`.
  - `test_topology_defensive_infeasible`: Evaluates EC-01 (`stack is None`), asserting diagnostic node returned without crashing.
  - `test_topology_defensive_none_layers`: Evaluates P1 (backend is `"None"`), asserting valid diagram without phantom nodes.
  - `test_node_label_sanitization`: Asserts quotes and brackets are safely escaped.
- `tests/test_web_studio.py`:
  - `test_api_topology_endpoint`: Asserts `POST /api/topology` returns 200 OK with `mermaid` and `svg` keys.
  - `test_scenarios_matrix_memoized`: Asserts `GET /api/scenarios/matrix` returns 6 rows with required fields and latency < 10ms.
  - `test_static_assets_vendored`: Asserts `/static/vendor/mermaid.min.js` returns 200 OK.
- Full regression suite:
  - `pytest -v` (asserts all existing 26 tests + new tests pass with 0 failures).

### End-to-End Visual Verification
- Start `stacksense web --port 8000`.
- Load scenarios P1 through P6: verify topology rendering, layer card formatting, and trade-off tables.
- Load edge cases (EC-01, EC-03): verify conflict relaxation advice displays actionable parameter deltas.
- Switch between Visual Studio form controls and JSON code editor: verify 250ms debounced sync without cursor jumps.
- Verify benchmark matrix tab loads pre-computed comparison data in <2ms.

### Submission Packaging Verification
- Execute `./scripts/package_submission.sh Aman_Kumar`.
- Verify exit code 0 and check generated zip in `dist/`.

--------------------------------------------------------------------------------

*Drafted with EGM · Remediated & Approved*
