# Research report — StackSense

## Purpose

This living report records the evidence used to build the technology catalogue and recommendation policies. It will be included or referenced in the final project report so that claims are attributable and reproducible.

## Research rules

1. Prefer primary sources: official documentation, pricing pages, service-level documentation, and licence texts.
2. Record the access date because pricing and platform features change.
3. Separate documented fact from interpretation or policy choice.
4. Do not use uncited LLM output as evidence.
5. Cite every external dataset, API, and library in the final report, as required by the event rules.

## Evidence record template

| Field | Record |
| --- | --- |
| Claim | |
| Technology / service | |
| Category | |
| Source URL | |
| Publisher | |
| Access date | |
| Extracted fact | |
| Applicability / caveat | |
| Licence / terms | |
| Reviewer and status | |

## Research tracks

### AI-era requirement discovery

The completed pre-release synthesis is in [ai-era-problem-research.md](ai-era-problem-research.md). It distinguishes primary-source architecture guidance from qualitative practitioner evidence and defines conditional AI-workload inputs. Treat it as a source of testable intake questions and policy hypotheses, not a vendor ranking.

### Catalogue facts

Research frontend, backend, database, hosting, cache, queue, search, storage, observability, and authentication candidates. For each, collect capabilities, limits, pricing basis, operational overhead, deployment model, compliance evidence, and ecosystem maturity.

Use [input-schema.md](input-schema.md) to ensure every researched fact can influence a real decision, and use [baseline-profiles.md](baseline-profiles.md) to focus the first catalogue pass. Store machine-readable records only when every material fact has a primary source, using [the catalogue schema](../data/technology-catalog/schema.json).

The first source-backed pass is maintained in [catalogue-evidence-ledger.md](catalogue-evidence-ledger.md). It is intentionally an evidence ledger rather than a completed recommendation catalogue so incomplete research cannot be mistaken for a verified decision rule.

### Compatibility and architecture patterns

Document supported integrations and architectural patterns—such as static frontend plus API, monolith, event-driven processing, and real-time workloads. Compatibility claims require sources or explicit policy rationale.

### Cost modelling

Collect published pricing units and free-tier conditions, but present results as ranges tied to workload assumptions. Avoid false precision where a provider calculator or unknown egress pattern is required.

### Evaluation scenarios

Design scenarios that vary one important variable at a time. Include prototype, budget-constrained project, high-growth SaaS, real-time application, compliance-heavy workload, on-premise deployment, and contradictory/no-solution cases.

## Citation ledger

Populate after the challenge begins.

| ID | Source | Used for | Licence / terms | Accessed | Status |
| --- | --- | --- | --- | --- | --- |
| R-001 | _Pending official sources_ | | | | |

## Known research risks

- Cloud pricing and product availability are region- and date-dependent.
- Compliance suitability cannot be inferred solely from marketing material.
- Popularity does not prove architectural fit.
- Public benchmarks can fail to represent a specific workload.
