---
title: "Architectural Decision Records"
tags: ["architecture", "adr", "madr"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# Architectural Decision Records

This directory contains Architectural Decision Records (ADRs) capturing significant architectural choices made across the lifecycle of `ed-schema`.

## Decision Format

Records adhere to Markdown Architectural Decision Records (MADR 3.0) format:

- **Context and Problem Statement:** Description of the forces, context, and requirements prompting the decision.
- **Decision Drivers:** Measurable qualities, constraints, and operational goals.
- **Considered Options:** Exhaustive enumeration of candidate solutions evaluated.
- **Decision Outcome:** Chosen solution with justification, positive consequences, negative consequences, and trade-offs.
- **Pros and Cons of the Options:** Detailed evaluation matrix for each option.

## Governance & Immutability

- **Numbering:** Zero-padded sequential four-digit integers: `0001-choice-of-technology.md`.
- **Immutability:** Once an ADR reaches `Accepted` status and merges to the main branch, it is immutable.
- **Superseding:** If a decision changes, author a new ADR referencing the prior decision. Update the prior record's status to `Superseded` pointing to the new ADR.
