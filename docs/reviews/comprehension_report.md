# Stage 6 Comprehension Test Report

- **Target Document**: `docs/product.md` (lines 1–68)
- **Reviewer**: Naive Reader (`egm-comprehension`)
- **Document Standard**: None (Self-containment audit in isolation)

---

### What this proposes

The document proposes StackSense, an intelligent recommendation engine that transforms high-level project requirements into a coherent, fully justified technology stack spanning frontend, backend, database, hosting, and supporting services. Rather than suggesting isolated tools, the system evaluates interoperability, enforces hard constraints (such as compliance, budget, and availability) before preferences, and surfaces trade-offs, cost bands, and alternatives. The engine is designed to be deterministic, reproducible, and capable of asking adaptive follow-up questions when faced with incomplete or contradictory project inputs.

### How the existing system works, per this document

Per this document, current practices rely on generic lists of "best technologies" or manual developer intuition that fail to expose trade-offs, operational compatibility, or hidden assumptions between lightweight prototypes and high-availability enterprise applications. Beyond acknowledging these generic lists and manual builder decision-making, the document does not describe an existing internal software system. StackSense is presented as a greenfield v1 product and evaluation submission being created to replace this manual, uncoordinated approach.

---

### Findings

#### Finding 1: Undefined Concept: "catalogue" and "catalogue version"
- **Severity**: Major
- **Affected Scope**: `## Product principles` (line 22) and `## Success measures` (line 67)
- **Discrepancy Description & Rationale**: The document mandates that recommendations must be reproducible based on "the same structured input and catalogue version" (line 22) and that reviewers must be able to reproduce recommendations from "stored inputs and catalogue version" (line 67). However, the "catalogue" is never defined, described, or linked anywhere in the brief. A fresh reader has no basis to understand what this catalogue contains (e.g., a static JSON/YAML file of curated components, a database, or an external package registry) or how catalogue versions are tracked and updated.

#### Finding 2: Assumed Context: "The final submission" and "public and hidden scenarios"
- **Severity**: Major
- **Affected Scope**: `## Success measures` (line 68)
- **Discrepancy Description & Rationale**: Line 68 states that "The final submission visibly addresses public and hidden scenarios, incomplete data, and impossible requests." A naive reader or incoming team member does not know what "final submission" refers to (e.g., a hackathon deliverable, academic contest, or client benchmark) or what constitutes "public and hidden scenarios." This introduces external competition/grading prerequisites that are not explained or grounded within the product brief.

#### Finding 3: Undefined Evidence Provenance: "evidence references" and "source reference"
- **Severity**: Nit
- **Affected Scope**: `## Outputs` (line 51), `## Non-goals for v1` (line 61), and `## Success measures` (line 66)
- **Discrepancy Description & Rationale**: The document requires recommendations to provide "evidence references" and every component to have a "machine-readable reason and source reference" (lines 51, 66), while explicitly excluding LLM responses from being considered technical evidence (line 61). However, the brief never clarifies where this technical evidence originates or what constitutes a valid source reference (e.g., whether sources are curated metadata entries within the technology catalogue or external documentation URLs).

#### Finding 4: Unspecified Delivery Form Factor
- **Severity**: Nit
- **Affected Scope**: `## Core user journey` (lines 26–30)
- **Discrepancy Description & Rationale**: The user journey describes an interactive loop ("starts a project profile", "answers a short set of high-signal questions", "asks adaptive follow-up questions", "receives a primary recommendation"), but omits the intended interface modality (e.g., web interface, CLI utility, or interactive API). While common in high-level briefs, a brief parenthetical or mention of the v1 form factor would clarify how the adaptive interaction is delivered.
