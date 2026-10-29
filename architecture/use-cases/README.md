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
