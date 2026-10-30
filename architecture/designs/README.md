---
title: "Software Design Documents"
tags: ["architecture", "designs", "sdd", "ieee-1016"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# Software Design Documents

This directory contains Software Design Documents (SDDs) detailing the structural, behavioral, and interface designs of subsystems within `ed-schema`.

## Design Standard

SDDs adhere to IEEE 1016 / Google Design Doc conventions, specifying:

- **Context & Scope:** Problem boundary, user personas, and operational context.
- **Goals & Non-Goals:** Explicit capabilities in scope versus deferred or rejected features.
- **Architectural Overview:** Structural diagrams, component breakdown, and hexagonal port/adapter wiring.
- **Detailed Design:** Class structures, state transitions, domain protocols, error contracts, and concurrency safety.
- **Cross-Cutting Concerns:** Security, latency, memory ceilings, telemetry, and platform portability (Linux/Proton/Windows NT).
- **Alternatives Considered:** Technical trade-offs rejected in favor of the selected approach.

## Design Specifications Catalog

- [`0001_scope_and_boundary_enforcement_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0001_scope_and_boundary_enforcement_architecture.md): SDD-001 Scope and Boundary Enforcement Architecture (implementation design for ADR 0008).
- [`0002_core_domain_and_ports_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0002_core_domain_and_ports_architecture.md): SDD-002 Core Domain and Ports Architecture (implementation design for ADRs 0001–0008).
- [`0003_core_use_cases_and_interactors_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0003_core_use_cases_and_interactors_architecture.md): SDD-003 Core Use Cases and Interactors Architecture (implementation design for UC-01–UC-04).
- [`0004_driven_adapters_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0004_driven_adapters_architecture.md): SDD-004 Driven Adapters Architecture (implementation design for secondary SPI implementations).
- [`0005_composition_root_and_driving_facade_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0005_composition_root_and_driving_facade_architecture.md): SDD-005 Composition Root and Driving Facade Architecture (implementation design for ADR 0006, SchemaEngine, and Container).
- [`0006_endpoint_contract_model_class_binding_architecture.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0006_endpoint_contract_model_class_binding_architecture.md): SDD-006 EndpointContract Model Class Binding Architecture (implementation design for ADR 0009).
