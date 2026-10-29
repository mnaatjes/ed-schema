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

## Naming Convention

Design specifications are named sequentially or by subsystem topic:

- `0001_subsystem_core_design.md`
- `schema_transformation_pipeline.md`
