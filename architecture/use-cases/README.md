---
title: "Use-Case Specifications"
tags: ["architecture", "use-cases", "up"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# Use-Case Specifications

This directory contains functional use-case specifications for `ed-schema` authored in accordance with the Unified Process and Cockburn sea-level goal methodology.

## Use-Case Standards

- **Goal Level:** Target sea-level user and caller goals (discrete operations delivering measurable caller value).
- **Format:** Fully dressed format detailing primary actors, trigger conditions, preconditions, main success scenario, extensions (alternative and failure flows), and postconditions.
- **Traceability:** Each use case must reference governing requirements, risks mitigated in `architecture/risk/`, and architectural decisions in `architecture/adr/`.

## Naming Convention

Use-case files are identified by a sequential identifier:

- `UC-01_<brief_description>.md`
- `UC-02_<brief_description>.md`

## Use-Case Catalog

- [`UC-01_load_manifests_and_register_schemas.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/UC-01_load_manifests_and_register_schemas.md): Ingestion of multi-namespace provider manifests and 4-tuple composite key registration.
- [`UC-02_compile_dataclass_models.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/UC-02_compile_dataclass_models.md): Pure in-process build-time compilation of JSON schemas into typed Python dataclasses.
- [`UC-03_verify_schema_parity.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/UC-03_verify_schema_parity.md): Automated structural AST parity verification between schemas and models.
- [`UC-04_validate_endpoint_pre_flight_contract.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/UC-04_validate_endpoint_pre_flight_contract.md): Composite pre-flight validation gate verifying headers and payloads prior to network dispatch.
