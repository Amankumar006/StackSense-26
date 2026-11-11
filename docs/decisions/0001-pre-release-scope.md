# ADR 0001: Keep the pre-release repository planning-only

**Status:** Accepted — 5 November 2026

## Context

The event rules state that submissions must be original and built during the challenge window. The detailed problem statement, input/output specification, sample scenarios, and report template are scheduled for release on 10 November 2026.

## Decision

Before the release, maintain documentation, research methodology, repository structure, testing strategy, and report templates only. Do not implement competition-specific recommendation rules, model outputs, or a finished interface before the official specification is available.

## Consequences

- The project starts the challenge with clear standards and low setup friction.
- The final engine can be designed against the actual evaluation contract.
- The repository avoids creating an appearance of pre-built competition work.
- Post-release implementation time must be managed tightly using the prepared architecture and scenario plan.
