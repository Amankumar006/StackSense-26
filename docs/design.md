# System design — StackSense

## Design target

Create an explainable, testable recommendation engine rather than a static decision tree or opaque chatbot. The official problem statement may constrain this design; its contract takes precedence once released.

## Proposed architecture

```text
UI / CLI / API adapter
        │
        ▼
Input schema + adaptive-question controller
        │
        ▼
Normaliser ──► contradiction / missing-information detector
        │
        ▼
Hard-constraint evaluator ──► infeasibility explanation
        │
        ▼
Compatible stack composer
        │
        ▼
Multi-objective scorer + tie-breaker
        │
        ▼
Explanation, cost-band, risks, and alternatives formatter
```

## Technology catalogue

The catalogue is the engine's evidence layer. Each technology record should include:

- component category and supported use cases;
- licence, managed/self-hosted availability, regions, and vendor-lock-in profile;
- cost model and documented cost assumptions;
- scale, reliability, data-model, and compliance capabilities;
- operational complexity and team-skill prerequisites;
- explicit incompatibilities and preferred integrations;
- source URLs, source dates, and confidence/review status.

Facts must be separated from subjective policy weights. This permits updates without rewriting recommendation logic.

The draft evidence-backed catalogue contract is [data/technology-catalog/schema.json](../data/technology-catalog/schema.json). The draft intake contract is [input-schema.md](input-schema.md). Both are planning artifacts until the official I/O contract is released.

## Decision pipeline

### 1. Validate and normalise

Convert free-form or form answers into typed values, ranges, and enums. Preserve unknown values instead of silently inventing them. Detect conflicts such as "zero monthly budget" with "managed multi-region high availability".

### 2. Ask only decision-changing questions

Use an information-gain rule: ask a question when its possible answers materially change feasible candidates or ranking confidence. Prefer defaults only when explicitly surfaced as assumptions.

### 3. Enforce hard constraints

Reject any component or full stack that violates a mandatory requirement, for example data residency, on-premise-only deployment, a banned vendor, unsupported language, required licence, or stated budget ceiling.

### 4. Compose compatible stacks

Create candidates from component records only when their compatibility edges allow it. Compatibility is a first-class rule: a highly ranked database and host cannot be combined when operational or regional constraints make the pair invalid.

### 5. Score and rank

For each feasible stack, compute a transparent weighted utility score:

```text
score = Σ (priority_weight × normalised_dimension_score) − documented_penalties
```

Initial dimensions: requirement fit, cost fit, scalability, delivery speed, team fit, operational burden, flexibility/lock-in, and ecosystem maturity. Weights are derived from user priorities and must be displayed. Use deterministic tie-breakers: fewer violated soft preferences, lower operational burden, lower estimated cost, then stable catalogue order.

### 6. Explain

Return the chosen stack alongside rejected alternatives, hard-constraint eliminations, key scoring factors, assumptions, risk flags, and a confidence signal. No recommendation may be returned without reasons.

## Output contract (draft)

```json
{
  "recommendation": {
    "frontend": {}, "backend": {}, "database": {}, "hosting": {}, "supporting_services": []
  },
  "assumptions": [],
  "constraints_applied": [],
  "reasons": [],
  "tradeoffs": [],
  "alternatives": [],
  "cost_estimate": {"range": "", "currency": "", "basis": []},
  "risks": [],
  "confidence": {"score": 0, "reasons": []},
  "catalogue_version": ""
}
```

## Edge-case policy

| Situation | Required behaviour |
| --- | --- |
| Missing critical input | ask a targeted question or state a visible assumption |
| Conflicting inputs | identify the conflict and request a resolution; never silently override |
| No feasible stack | return an infeasibility report and the smallest requirement changes that would unlock options |
| Budget unknown | show a usage- and region-qualified range, not a fabricated total |
| Extreme scale | favour proven operational patterns and flag validation requirements |
| Compliance-sensitive workload | require verification and avoid claims beyond catalogue evidence |
| Equal-score candidates | expose the tie-breaker and show both options |

## Quality attributes

- **Correctness:** hard constraints are never broken.
- **Explainability:** every choice maps to input facts and catalogue evidence.
- **Reproducibility:** deterministic result for the same input, policy, and catalogue version.
- **Extensibility:** catalogue and policy can grow without UI rewrites.
- **Testability:** pure decision functions are separated from interface code.

## Deferred implementation decisions

- The user interface and runtime entry point will follow the official I/O and packaging specification.
- External APIs, datasets, and dependencies are deferred until they can be cited and justified.
