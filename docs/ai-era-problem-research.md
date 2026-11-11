# AI-era problem research — StackSense

**Research date:** 5 November 2026  
**Purpose:** Identify what a modern technology-stack recommender must ask before selecting frontend, backend, database, hosting, and AI-adjacent infrastructure. This is pre-release research methodology, not a competition-specific implementation.

## 1. What the published challenge actually asks

The official event page describes an engine that accepts project scale, team size, budget, and infrastructure constraints, then recommends frontend, backend, database, and hosting tools with architectural reasoning. It explicitly assesses recommendation fit (35%), input design and research (30%), reasoning and explainability (20%), and documentation (15%). The detailed I/O contract, sample cases, and report template are not yet published; they are scheduled for 10 November 2026. [Official event page](https://unstop.com/hackathons/stacksense-challenge-synergy-26-international-institute-of-information-technology-iiit-bangalore-1762891/amp)

**Interpretation:** The winning problem is not “name the best stack.” It is a constrained decision system that can defend why a stack fits a given project and why plausible alternatives do not.

## 2. The AI-era change in stack selection

AI is not a universal layer to add by default. AI-enabled applications introduce requirements that conventional intake forms routinely miss:

- model access and provider portability;
- token- and tool-call-based variable cost;
- retrieval, document ingestion, embeddings, citations, and evaluation for knowledge applications;
- tool permissions, approval gates, auditability, retries, and failure containment for agents;
- sensitive-data handling, residency, and prompt-injection exposure; and
- traces, quality evaluations, and fallback behaviour as production requirements.

Primary guidance supports a conditional approach. Microsoft distinguishes fixed RAG from agentic RAG: the latter is intended for multi-step reasoning, dynamic source selection, query decomposition, or retrieval combined with actions—not every search use case. It also calls out additional agent latency, cost, reliability, observability, and security concerns. [RAG design guide](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide), [agentic RAG considerations](https://learn.microsoft.com/uk-ua/azure/architecture/ai-ml/guide/rag/rag-agentic)

Google's agentic architecture guidance similarly treats frontend, agent framework, tools, memory, runtime, model, and model runtime as separate decisions whose choices affect performance, scale, cost, and security. [Google Cloud guidance](https://docs.cloud.google.com/architecture/choose-agentic-ai-architecture-components)

## 3. Ground-level practitioner signals

The following are qualitative discovery evidence from public discussion, not capability or benchmark proof. They should influence questions and hypotheses only; all catalogue facts must later be verified through primary sources.

| Signal | Practitioner evidence | StackSense implication | Confidence |
| --- | --- | --- | --- |
| Evaluation and operational reliability dominate model calls | Practitioners report that evaluation, rate limits, ingestion, streaming, monitoring, retries, and state handling create more production work than the basic model integration. [RAG war stories](https://www.reddit.com/r/Rag/comments/1htqgzm), [failure-handling discussion](https://www.reddit.com/r/ClaudeMCP/comments/1uw2dfm/built_a_production_rag_llm_pipeline_with/) | Ask whether output drives decisions/actions, expected failure behaviour, monitoring ownership, rollback needs, and whether an evaluation set exists. | Medium as a problem-discovery pattern; low for individual claims. |
| Retrieval needs are workload-specific | A production-RAG discussion emphasizes layout/table parsing, exact-ID lookup, metadata filtering, reranking, and citations; vector-only retrieval may be unsuitable for exact lookup. [Discussion](https://www.reddit.com/r/Rag/comments/1p4myqq/production_level_rag_setup_share_your_best_bits/) | Ask document formats, table/image density, update cadence, exact-match requirements, citation requirement, data scale, and access rules. Do not automatically recommend a dedicated vector database. | Medium as a question-design signal. |
| Team operating ability matters more than fashionable decomposition | An experienced-engineer retrospective describes lower operational burden with a modular monolith until concrete scaling, isolation, ownership, or deployment reasons emerged. [Discussion](https://www.reddit.com/r/ExperiencedDevs/comments/1rmfbpu/what_architectural_decision_looked_wrong_at_first/) | Default small/new teams toward simpler deployable architecture unless a stated constraint warrants services. | Medium as a design heuristic; not universal. |
| Local/self-hosted model economics are conditional | Practitioners cite concurrency, utilization, hardware amortisation, power/cooling, quality, and operational labour; privacy or residency can be a more important driver than price. [Cost discussion](https://www.reddit.com/r/LocalLLM/comments/1x1n1rg/selfhosted_llm_cost_per_token/), [break-even discussion](https://www.reddit.com/r/LocalLLM/comments/1wly4hy/at_what_point_does_selfhosting_become_cheaper/) | Ask token mix, monthly volume, peak concurrency, existing hardware, target quality, data restrictions, and on-call capability. Present cloud vs regional/VPC vs self-hosted as alternatives with assumptions. | Medium for input design; low for a numeric break-even. |
| Automation must be gated by consequence | Founder and practitioner discussions emphasise team capability, testing, and gated automation rather than unrestricted agent actions. [Discussion](https://www.reddit.com/r/ycombinator/comments/1uy0qs5/what_tech_stack_would_you_choose_for_building_an/) | Ask error consequence, actions permitted, human-approval policy, audit requirement, and workflow durability. | Medium as a safety-oriented design signal. |

Public X search did not produce sufficiently verifiable practitioner evidence. X posts are therefore excluded from decision rules; Reddit findings above are deliberately tagged as qualitative sentiment.

## 4. Proposed adaptive intake additions

These additions should be conditional: only show them when the project uses or is considering AI.

### AI workload classifier

- No AI capability
- Assistive generation or chat
- Extraction, classification, or summarisation
- RAG / knowledge assistant
- Tool-using or agentic workflow
- Self-hosted or custom model serving

### Risk and governance

- What is the consequence of an incorrect answer or action? (low / human-review required / financially, legally, medically, or safety sensitive)
- May the system call external tools or mutate data?
- Is human approval mandatory before an action?
- Are logs, traces, prompt history, and audit evidence required?
- Are there PII, confidential documents, residency, or external-model restrictions?

### Retrieval and evaluation

- What is the source-data type: plain text, PDFs, tables, images, structured records, or code?
- Are exact identifiers, citations, and access-control filtering required?
- How often do documents change and what deletion/update behaviour is needed?
- Is there a representative evaluation set and acceptance target for quality, latency, and cost?

### Economics and operations

- Expected monthly input/output tokens, request volume, peak concurrency, and latency budget.
- Existing cloud commitments, GPU/hardware availability, and provider restrictions.
- Team experience with model operations, data pipelines, and on-call responsibilities.
- Prototype, MVP, or production maturity; target release date and service-level objective.

## 5. Candidate decision rules to validate after release

These are policies to test—not facts about any named vendor or technology.

1. Recommend deterministic code or a fixed workflow when the task is structured and predictable; only introduce agent orchestration when dynamic tool choice or multi-step reasoning is actually required.
2. Require a risk/approval design, evaluation plan, observability, timeouts, and fallback behaviour for tool-using AI workflows.
3. Treat AI cost as usage-dependent. Avoid claiming a precise total without model, provider, region, token, tool, and concurrency assumptions.
4. For sensitive retrieval workloads, require evidence of access control, data handling, and security measures; treat retrieved text as untrusted input.
5. Prefer a conventional database with vector capability when it meets the retrieval need and reduces operational burden; only recommend dedicated vector infrastructure where scale, performance, feature, or isolation requirements justify it.
6. Prefer a modular monolith for small teams unless independent scaling, fault isolation, organisational ownership, or deployment constraints provide a concrete reason to split services.

## 6. Evidence boundaries

- Vendor architecture documents establish available design considerations, not that their products are universally best.
- Reddit is useful for discovering failure modes and language users employ; it does not establish pricing, performance, security, or compliance facts.
- The final catalogue must maintain per-technology primary-source citations, access dates, and applicable workload/region assumptions.
- Final rules, input schema, and outputs must be reconciled with the official problem statement after 10 November.

## 7. Research-to-product conclusion

StackSense should lead with: **“What could fail, what must be protected, and who will operate this?”** Then it can select technologies. This produces a stronger engine than one that begins with framework popularity. Its principal advantage in the AI era is not recommending the most tools—it is avoiding unnecessary AI, agent, microservice, and infrastructure complexity while making necessary complexity explicit and supportable.
