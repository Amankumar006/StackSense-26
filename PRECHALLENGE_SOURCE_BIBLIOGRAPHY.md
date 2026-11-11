# Private pre-challenge source bibliography — do not submit or copy

**Status:** Personal reading index created before the challenge window.  
**Integrity rule:** This is not a final references section, technology catalogue, or knowledge base. In the challenge window, revisit and cite original sources independently in the new repository; do not copy these annotations or structure.

## Decision methods and distributed systems

- Saaty, T. L. (1987). *The analytic hierarchy process—what it is and how it is used.* [DOI](https://doi.org/10.1016/0270-0255%2887%2990473-8). Read for: multi-criteria prioritisation and inconsistency in pairwise judgement.
- Gilbert, S. and Lynch, N. (2002). CAP theorem background via [AWS overview](https://docs.aws.amazon.com/whitepapers/latest/availability-and-beyond-improving-resilience/cap-theorem.html). Read for: partition-time consistency/availability trade-off.
- Abadi, D. J. (2012). *Consistency Tradeoffs in Modern Distributed Database System Design.* [Article/PDF link](https://www.odbms.org/2012/01/consistency-tradeoffs-in-modern-distributed-database-system-design/). Read for: normal-operation latency/consistency reasoning.

## Application and platform architecture

- [AWS Well-Architected Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/). Read for: recovery-process and change-management considerations.
- [Azure cloud design patterns](https://learn.microsoft.com/azure/architecture//patterns). Read for: queue-based load leveling, retry, circuit breaker, and composition caveats.
- [Azure Retry pattern](https://learn.microsoft.com/th-th/azure/architecture/patterns/retry). Read for: bounded retries and idempotency.
- [OpenTelemetry overview](https://opentelemetry.io/docs/what-is-opentelemetry/). Read for: traces, metrics, logs, and backend-independent instrumentation.

## AI/RAG and agent systems

- [Microsoft RAG design and evaluation guide](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide). Read for: fixed RAG versus agentic RAG and staged evaluation.
- [Microsoft agentic RAG considerations](https://learn.microsoft.com/uk-ua/azure/architecture/ai-ml/guide/rag/rag-agentic). Read for: tool-call latency, cost, reliability, observability, and security concerns.
- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices). Read for: evaluation as a structured production practice.
- [OpenAI agent safety](https://developers.openai.com/api/docs/guides/agent-builder-safety). Read for: prompt injection, structured outputs, tool permissions, and human review.

## Primary product documentation to revisit on release day

- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
- [FastAPI features](https://fastapi.tiangolo.com/features/)
- [Next.js rendering](https://nextjs.org/learn/dashboard-app/static-and-dynamic-rendering)
- [Cloud Run autoscaling](https://docs.cloud.google.com/run/docs/about-instance-autoscaling)
- [Amazon RDS backups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [SQS queue semantics](https://docs.aws.amazon.com/en_gb/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)

## Clean-room use

On release day, first read the official StackSense problem statement. Then independently choose which original sources are relevant, verify their currency and scope, record citations anew, and author every final claim in the fresh repository.
