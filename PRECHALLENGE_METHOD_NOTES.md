# Private pre-challenge methodology notes — do not submit or copy

**Status:** Personal study notes, written before the challenge window.  
**Integrity rule:** These notes may inform independent work after 10 November 2026, 10:00 AM IST. Do **not** copy this file, its prose, tables, or any derived artefact into the fresh submission repository.

## Question this study addresses

How should a person reason about competing technology options without reducing architecture to a popularity contest?

## AHP: useful, but only in the right role

The Analytic Hierarchy Process (AHP) is a multi-criteria decision method based on hierarchical priorities and pairwise comparisons. Its literature discusses measuring inconsistency in judgments; this is useful when a decision-maker supplies nuanced priorities that may conflict.

**Potential lesson for later independent design:** A pairwise-priority approach can help explain how a user's preferences were elicited. It should not override non-negotiable requirements such as residency, deployment restrictions, or explicit cost caps. A long pairwise questionnaire may also be inappropriate for a short hackathon product; a simple ranked-priority interface can be more usable and auditable.

**Study sources:** [Saaty (1987)](https://doi.org/10.1016/0270-0255%2887%2990473-8), [Saaty (1991)](https://link.springer.com/article/10.2333/bhmk.18.29_1).

## CAP: do not use the misleading “pick any two” shortcut

CAP concerns distributed systems under a network partition. A precise practical interpretation is that, when partitioned, a system faces a choice between consistency and availability; it is not a generic three-option selector for every database or a claim about single-node applications.

**Potential lesson for later independent design:** Ask about multi-region/distributed data, write/read correctness requirements, offline/partition behaviour, and availability targets only when the project actually needs distributed operation. Do not expose CAP terminology to non-specialist users unless it explains a concrete trade-off.

**Study sources:** [AWS CAP overview](https://docs.aws.amazon.com/whitepapers/latest/availability-and-beyond-improving-resilience/cap-theorem.html), [CAP critique](https://www.cl.cam.ac.uk/research/dtg/archived/files/publications/public/mk428/cap-critique.pdf).

## PACELC: latency matters even without a partition

PACELC extends the discussion beyond partition events: in normal operation, replication/consistency choices can still carry latency trade-offs. It is a design lens, not a catalogue label for a vendor.

**Potential lesson for later independent design:** For latency-sensitive, geographically distributed, strongly consistent workloads, surface the trade-off as a question about measured latency, region placement, and correctness needs—not as an unsupported technology claim.

**Study sources:** [Abadi, Consistency Tradeoffs in Modern Distributed Database System Design](https://www.odbms.org/2012/01/consistency-tradeoffs-in-modern-distributed-database-system-design/), [Proving PACELC](https://uwaterloo.ca/distributed-algorithms-systems-lab/sites/default/files/uploads/files/proving_pacelc.pdf).

## Clean-room reminders for the challenge window

- Start from a new repository after the window opens.
- Re-author all final documentation, catalogue/knowledge-base data, code, tests, and report material from scratch.
- Use sources again from their original links; cite them in the final report.
- Let official inputs/outputs and samples determine the final engine, not this pre-release study.
- Prefer a smaller system whose assumptions and limitations are explicit over a complicated system that cannot be verified.
