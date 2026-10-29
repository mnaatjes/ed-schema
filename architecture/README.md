---
title: "Architecture Governance Root"
tags: ["architecture", "governance", "up"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# Architecture Governance Root

This directory constitutes the maintainer and engineering plane for `ed-schema`, strictly governed by the Unified Process (UP) architectural documentation taxonomy.

## Document Taxonomy

The engineering plane is partitioned into six canonical types:

1. [`risk/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/README.md): Master Risk Register quantifying architectural and operational exposure ($RE = P \times I$).
2. [`use-cases/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/README.md): RUP functional use-case specifications (Cockburn sea-level user goals).
3. [`adr/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/README.md): Immutable Architectural Decision Records adhering to MADR 3.0.
4. [`designs/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/README.md): IEEE 1016 Software Design Documents detailing subsystem realization.
5. [`rfcs/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/rfcs/README.md): Collaborative Request for Comments exploring architectural options.
6. [`api/`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/api/README.md): Boundary interface contracts (OpenAPI 3.1, JSON Schema, AsyncAPI).

## Boundary Invariants

- **Dual-Root Decoupling:** Customer and operator documentation resides exclusively under `docs/` governed by Diataxis. Engineering records, draft proposals, and technical ledgers reside strictly under `architecture/`.
- **Frontmatter Standard:** Every markdown document must declare YAML frontmatter with `title`, `tags`, `created_at`, and `last_updated_at`.
- **Immutability Policy:** Accepted ADRs are immutable. Superceded decisions must be marked `Deprecated` or `Superseded` with an explicit pointer to the replacement ADR.
