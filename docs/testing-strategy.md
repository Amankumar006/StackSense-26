# Testing strategy — StackSense

## Goal

Prove that recommendations respect hard constraints, remain reproducible, and produce useful explanations across ordinary and adversarial scenarios.

## Test layers

| Layer | Focus | Example |
| --- | --- | --- |
| Unit | validation, normalisation, individual rules | budget parser preserves unknown values |
| Catalogue | schema, citations, compatibility graph | every selectable item has category and source |
| Decision | filtering, scoring, tie-breaking | on-prem-only excludes cloud-only options |
| Scenario | complete input-to-output behaviour | small prototype vs regulated high-availability service |
| Regression | protect resolved bugs | a prior contradiction never receives a silent recommendation |
| Presentation | UI and report evidence | screenshots match final engine output |

## Must-have scenario matrix

1. Small team, low budget, short deadline.
2. High-growth public web application with variable traffic.
3. Data-heavy application requiring strong relational consistency.
4. Real-time or event-driven workload.
5. Sensitive-data workload with regional and compliance restrictions.
6. On-premise or hybrid-only deployment.
7. Team with strong language preference but an incompatible hard constraint.
8. Contradictory requirements.
9. No feasible recommendation.
10. Incomplete inputs that require follow-up questions.
11. Equal-scoring alternatives with a visible tie-breaker.

## Acceptance gates

- No hard-constraint violation in any scenario.
- Every output includes assumptions, reasons, and catalogue version.
- Same input, policy version, and catalogue version yields the same result.
- Infeasible inputs return a clear explanation, not an empty or fabricated answer.
- Final screenshots and report examples are reproducible from versioned scenarios.
