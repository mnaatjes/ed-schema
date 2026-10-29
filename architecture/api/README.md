---
title: "API & Boundary Contracts"
tags: ["architecture", "api", "contracts"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# API & Boundary Contracts

This directory contains formal, machine-readable interface specifications and schemas representing external boundary contracts.

## Supported Contract Formats

- **OpenAPI 3.1+:** REST API contracts for HTTP endpoints.
- **JSON Schema (Draft 2020-12 / Draft 7):** Payload validation and data serialization models.
- **AsyncAPI 2.x/3.x:** Event streaming contracts (e.g. EDDN event streams, SSE endpoints).

## Organization Standards

Contracts are partitioned by protocol and service origin:

- `openapi/`: OpenAPI 3.1 specification documents (YAML/JSON).
- `schemas/`: Canonical JSON Schema files describing boundary payloads.
- `asyncapi/`: Asynchronous event channel specifications.
