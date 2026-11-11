# Baseline project profiles

These are research and testing lenses, not pre-decided answers. They will be mapped to the official sample scenarios and contract after release.

| Profile | Dominant constraints | Research questions to answer |
| --- | --- | --- |
| Lean prototype | 1–3 builders, short deadline, low/uncertain budget, best-effort reliability | Which integrated managed offerings minimize setup while preserving a migration path? |
| Standard SaaS | web/API, relational core data, moderate growth, small product team | When is a modular monolith with managed relational storage sufficient? What triggers cache, queue, or service separation? |
| Compliance-sensitive product | regulated/confidential data, residency, auditability, strong access controls | Which deployment, identity, logging, encryption, and data-location facts are documented? What is explicitly outside StackSense's compliance claim? |
| High-scale or real-time service | bursty traffic, low latency, high availability, real-time/background workloads | Which candidates support autoscaling, caching, asynchronous processing, recovery, and observability within the stated budget? |
| Knowledge/RAG application | evolving documents, citations, mixed formats, retrieval quality constraints | Does it need RAG? What ingestion, search, metadata, access control, evaluation, and cost requirements change the stack? |
| Tool-using AI workflow | external actions, variable latency/cost, audit and approval needs | What guardrails, durable workflow, tool authorization, tracing, evaluation, and fallback policy are required? |
| Privacy-first or on-premise deployment | no external model/API, existing hardware, strict residency | What is feasible given model quality, GPU capacity, operations skill, updates, and reliability expectations? |

## Baseline evaluation rule

Each profile must later have at least one feasible recommendation, one credible alternative, and one clear non-recommendation with reasons. A profile may legitimately yield no feasible stack; that result is preferable to an unsupported compromise.
