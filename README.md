# StackSense

An explainable, deterministic technology-stack recommendation engine for the **StackSense Challenge at Synergy '26 (IIIT Bangalore)**.

StackSense takes structured project parameters (scale, team experience and languages, budget, timeline, deployment constraints, and regulatory obligations) and returns a compatible, defensible combination of **frontend**, **backend**, **database**, **hosting**, and **supporting services**. Every choice is backed by input field drivers (`driven_by`), at least one viable alternative with a concrete rejection reason (`why_not`), and honest trade-offs.

---

## 1. System Architecture

```text
                     ┌──────────────────────────────────────────────┐
                     │         Scenario Input (CLI / UI Form)       │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │ 1. Schema Validator & Normalizer             │
                     │    - Validates Section 3.1 types and enums   │
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

### Module Descriptions & Data Flow
1. **Schema Validator & Normalizer (`stacksense.validation`)**: Ingests raw JSON dictionaries, validates field types, ranges, and mandatory schemas against Section 3.1, assigns documented defaults recorded into `assumptions[]`, and detects invalid inputs or contradictions.
2. **Hard-Constraint Filter (`stacksense.constraints`)**: Enforces non-negotiable boundaries per §5.3: `data_residency`, `compliance` (e.g. RBI localization, PCI DSS), `deployment_model` (on-premise / air-gapped), and explicit `cloud_preference`. Infeasible candidates are pruned before scoring.
3. **Layer Scorer & Compatibility Composer (`stacksense.engine`)**: Applies multi-criteria utility scoring across viable candidates per layer based on platform support, language alignment, team experience, and priority weights (1–5). Verifies pairwise compatibility across layers.
4. **Explanation & Cost Band Estimator (`stacksense.engine`)**: Binds architectural justifications to specific input field paths (`driven_by`), identifies the closest viable alternative with a comparative `why_not` rationale, and estimates monthly infrastructure cost bands in USD (`min`, `max`, `assumptions`).
5. **Output Serializer & CLI (`stacksense.cli`)**: Formats and exports results strictly matching the Section 4 JSON specification.

---

## 2. Technology Stack & Versions

- **Engine Language:** Python 3.11+ (tested on Python 3.11 and 3.12)
- **Data Validation & Schemas:** Pydantic 2.13+
- **Test Harness:** Pytest 9.1+
- **Build System:** Setuptools $\ge 68.0$

---

## 3. Prerequisites

- **OS:** Linux, macOS, or Windows (WSL2 recommended on Windows).
- **Python:** Python 3.11 or newer (`python3 --version`).
- **RAM / CPU:** Runs comfortably on any standard laptop ($< 100$MB memory, completes in $< 0.5$ seconds).
- **No Paid API Keys Required:** Runs 100% locally and offline out of the box.

---

## 4. Step-by-Step Local Setup

### Option A: Python Virtual Environment (Recommended, <1 minute)
```bash
# 1. Open the project root (source/ in the submission bundle)

# 2. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install package in editable mode
python -m pip install --upgrade pip
python -m pip install -e .
```

### Browser Studio

From the project root, activate the virtual environment and run:

```bash
python -m pip install fastapi==0.141.1 uvicorn==0.34.0
python -m uvicorn stacksense.web:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 to load a scenario preset or edit a scenario in the form or JSON editor. In the submission bundle, the report sits alongside `source/`.

### Option B: Docker Compose Setup (Zero local Python dependencies)
```bash
# 1. Build Docker image
docker compose build

# 2. Run batch evaluation on all public scenarios
docker compose up engine

# 3. Run full test suite in container
docker compose run test
```

---

## 5. How to Run Scenarios & Generate Outputs

### Run a Single Scenario JSON
To run a scenario and display the recommendation with explanations:
```bash
python -m stacksense.cli run data/scenarios/P2.json
```

To export the result directly to a Section 4 compliant JSON file:
```bash
python -m stacksense.cli run data/scenarios/P2.json --output outputs/P2_output.json
```

### Run Batch on All Public Scenarios (P1–P6)
To run all benchmark scenarios in one command and generate all `outputs/P*_output.json` files:
```bash
python -m stacksense.cli batch data/scenarios/ --output-dir outputs/
```

### Run Automated Tests
```bash
python -m pip install -e '.[test]' httpx
python -m pytest -v
```

---

## 6. How to Switch Off All LLM Features (Section 5.1 Test)

StackSense's recommendation and scoring engine is **100% deterministic custom code** (rule-based hard filtering + weighted multi-objective scoring). 

To guarantee that no LLM calls are made:
- By default, the CLI runs in `--no-llm` mode.
- You can explicitly pass the flag:
  ```bash
  python -m stacksense.cli run data/scenarios/P1.json --no-llm
  ```
- Or set the environment variable:
  ```bash
  export ENABLE_LLM=false
  ```
The engine produces 100% identical JSON outputs with LLMs disabled, satisfying Section 5.1 evaluation requirements.

---

## 7. Project Structure Overview

```text
StackSence-'26/
├── pyproject.toml                         # Project package configuration and scripts
├── README.md                              # This setup and run guide
├── src/stacksense/                        # Core Python application package
│   ├── __init__.py                        # Package initialization
│   ├── catalog.py                         # Technology catalogue query interface
│   ├── constraints.py                     # Hard-constraint pruning (residency, compliance, cloud)
│   ├── engine.py                          # Recommendation pipeline & multi-criteria scoring
│   ├── validation.py                      # Input validation & contradiction detection (FR7)
│   ├── cli.py                             # CLI runner for single and batch scenarios
│   └── models/                            # Typed Pydantic schemas (FR1, FR2, FR8)
│       ├── enums.py                       # Official enum definitions
│       ├── input.py                       # Section 3.1 input schema models
│       └── output.py                      # Section 4 output schema models
├── data/
│   ├── scenarios/                         # Public scenarios P1–P6 JSON files
│   │   ├── P1.json ... P6.json
│   │   └── stacksense_public_scenarios.json
│   └── technology-catalog/                # Technology knowledge base & citations
│       ├── schema.json                    # Catalogue metadata JSON schema
│       └── catalogue.json                 # 33 verified technologies with primary-source links
├── outputs/                               # Generated JSON outputs for public scenarios
│   ├── P1_output.json ... P6_output.json
├── docs/                                  # Reconciled specifications and contest documents
│   ├── official-problem-statement.pdf     # Official challenge problem statement (PDF v1.0)
│   ├── official-problem-statement.txt     # Extracted text specification
│   ├── official-contract-reconciliation.md# Release-day reconciliation report
│   ├── product.md                         # Reconciled product specification
│   ├── input-schema.md                    # Section 3.1 schema dictionary
│   ├── design.md                          # Detailed pipeline & scoring design
│   └── testing-strategy.md                # Test matrices and regression plan
└── tests/                                 # Pytest test suite
    ├── test_determinism.py                # Verifies identical output across runs (FR9)
    ├── test_public_scenarios.py           # Integration tests on P1 through P6
    └── test_validation.py                 # Edge-case and contradiction tests
```

---

## 8. Credits & Attribution

All third-party tools, libraries, and datasets used in StackSense are publicly available and open-source:
- **Pydantic:** Open-source data validation and schema management ([MIT License](https://github.com/pydantic/pydantic/blob/main/LICENSE)).
- **Pytest:** Open-source Python testing framework ([MIT License](https://github.com/pytest-dev/pytest/blob/main/LICENSE)).
- **Technology Documentation & Pricing References:** Official documentation for AWS, Google Cloud, Microsoft Azure, PostgreSQL, Redis, Netlify, Astro, Next.js, FastAPI, Spring Boot, Razorpay, Stripe, and Meilisearch (all cited in `data/technology-catalog/catalogue.json` and `docs/research-report.md`).
