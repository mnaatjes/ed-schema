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

- **Numbering:** Zero-padded sequential four-digit integers: `0001_title_description.md`.
- **Immutability:** Once an ADR reaches `Accepted` status and merges to the main branch, it is immutable.
- **Superseding:** If a decision changes, author a new ADR referencing the prior decision. Update the prior record's status to `Superseded` pointing to the new ADR.

## ADR Catalog

- [`0001_multi_namespace_manifest_loading_and_composite_schema_registry.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0001_multi_namespace_manifest_loading_and_composite_schema_registry.md): Universal 4-tuple composite key indexing and multi-namespace manifest ingestion.
- [`0002_programmatic_build_time_dataclass_compilation.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0002_programmatic_build_time_dataclass_compilation.md): Pure in-process programmatic build-time compilation of Python dataclasses.
- [`0003_granular_in_process_parity_verification.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0003_granular_in_process_parity_verification.md): Automated AST-equivalence parity verification across provider namespaces.
- [`0004_dto_naming_conventions_and_lexical_scope_isolation.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0004_dto_naming_conventions_and_lexical_scope_isolation.md): Strict wire DTO vs game domain model demarcation and PEP 8 naming formulas.
- [`0005_composite_pre_flight_endpoint_and_header_contract_validation.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0005_composite_pre_flight_endpoint_and_header_contract_validation.md): Unified pre-flight validation gate for HTTP header parameters and JSON schema payload bodies.
