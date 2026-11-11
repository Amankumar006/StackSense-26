# Private pre-challenge failure-mode notes — do not submit or copy

**Status:** Personal study notes, written before the challenge window.  
**Integrity rule:** Do not copy this file, its prose, or derivatives into the fresh final repository. Use it only to improve independent reasoning after the official release.

## Why this study matters

Technology choice is partly a choice about how a system fails and who can recover it. A recommendation that names services without asking about failure handling, recovery objectives, operational ownership, or action risk is incomplete.

## Transient faults are not permanent faults

Cloud dependencies can fail transiently due to contention, temporary unavailability, timeouts, or short network disruptions. Retrying can help only when the operation is safe to repeat and the retry policy is bounded. Multiple uncoordinated retry layers can amplify load during an outage; persistent failure needs a different response such as a circuit breaker, graceful degradation, or escalation.

**Private reasoning prompt:** What may be retried? Is it idempotent? Where is the retry budget? What happens after retries end?

**Study sources:** [Azure Retry pattern](https://learn.microsoft.com/th-th/azure/architecture/patterns/retry), [Azure transient-fault handling](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults), [Azure Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker).

## Recovery is a workflow, not a backup checkbox

Reliability guidance emphasizes resilient architecture, consistent change management, and proven recovery processes. A recovery claim needs ownership, an objective, a tested restoration path, and awareness of dependencies outside the database or storage system.

**Private reasoning prompt:** Who restores? How much data loss is tolerable? How quickly must service return? Has restoration/cutover been practiced?

**Study source:** [AWS Well-Architected Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/).

## Queues change failure handling; they do not remove it

Queues can decouple work and absorb bursts, but consumer failure, duplicate delivery, ordering, retention, poison messages, and operational visibility remain design concerns. The relevant question is not simply “use a queue?” but what delivery and recovery semantics the workload needs.

**Private reasoning prompt:** Is work repeatable? Does order matter? How are poison messages inspected and resolved? What data is lost if a worker fails mid-operation?

**Study source:** [Azure cloud design patterns](https://learn.microsoft.com/azure/architecture//patterns).

## AI retrieval and tools add a distinct trust boundary

Untrusted documents, web pages, tool responses, and connectors can contain prompt injection. Structured data flow, least-privilege tools, approvals for consequential actions, and evaluation/trace review can reduce risk but do not eliminate it.

**Private reasoning prompt:** What inputs are untrusted? Which tool action is irreversible? What data can leave the system? Is a human required before impact?

**Study sources:** [OpenAI agent safety](https://developers.openai.com/api/docs/guides/agent-builder-safety), [OpenAI deep-research safety](https://developers.openai.com/api/docs/guides/deep-research).

## Clean-room reminder

After 10 November, learn from these questions but independently author the project’s final input design, constraints, explanations, tests, and documentation in the new repository. The official competition contract remains the source of truth.
