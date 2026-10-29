---
title: "ADR 0005: Composite Pre-Flight Endpoint and Header Contract Validation"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["RFC 0001 (ed-schema)", "ADR 0001 (ed-schema)", "OpenAPI 3.1 Specification"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "headers", "validation", "pre-flight", "contracts", "hexagonal"]
---

# ADR 0005: Composite Pre-Flight Endpoint and Header Contract Validation

## Context and Problem Statement

When an application communicates with external APIs (`Frontier CAPI`, `Inara`, `EDDN`, `Spansh`), data contracts govern both:
1. **HTTP Headers:** Authentication tokens (`Authorization: Bearer`), content negotiation (`Content-Type`, `Accept`), client identification (`User-Agent`), and rate-limit metadata.
2. **Payload Bodies:** Request bodies (`POST`, `PUT`) or query parameters complying with formal JSON Schemas.

Headers introduce distinct challenges:
- **Case-Insensitivity & Multi-Valued Tokens:** Header keys are case-insensitive with string values or comma-delimited lists.
- **Variable Lifecycles & Sources:** Headers range from static constants (`Content-Type: application/json`) to injected client secrets (`Authorization: Bearer <token>`) and dynamic session tokens.

Historically, client libraries validated payloads and headers separately, or deferred validation until network transmission. When requests failed due to missing headers, unescaped tokens, or schema mismatches, failures occurred only *after* opening network sockets in `ed-transport`.

How should `ed-schema` abstractly model, organize, and validate HTTP header rules alongside payload schemas to provide a unified **pre-flight validation gate** before wire dispatch?

---

## Decision Drivers

* **Fail-Fast Local Pre-Flight Invariant:** Any missing header, regex format violation, or payload schema violation must fail fast locally in microseconds before opening network connections.
* **OpenAPI 3.1 Alignment:** Model headers as first-class operation parameter contracts (`in: header`).
* **The Three Cardinal Header Categories:** Decouple static protocol constants, injected authentication credentials, and dynamic transport state.
* **Composite Validation Interactor:** Provide a single unified use case (`ValidateEndpointCallUseCase`) validating both headers and body payloads simultaneously.
* **Zero Secret Storage:** Validate the *shape* and *constraints* (regex) of headers without storing sensitive secrets in `ed-schema`.

---

## Considered Options

* **Option 1: Payload-Only Validation in `ed-schema`.** Restrict `ed-schema` strictly to JSON Schema body validation, leaving header construction and validation to ad-hoc dictionaries in client libraries.
  *(Rejected: High error rate; missing or malformed headers escape to remote servers and fail with 401/400 errors).*
* **Option 2: Transport-Layer Validation in `ed-transport`.** Force `ed-transport` to validate headers against endpoint schemas.
  *(Rejected: Violates hexagonal boundaries; `ed-transport` is a physical network delivery engine, not a schema registry. It lacks context on which specific headers are required by individual API endpoints).*
* **Option 3: Composite Pre-Flight Contract Modeling in `ed-schema`.** Model headers via `HeaderParameterContract` and composite `EndpointContract` entities, offering a single `ValidateEndpointCallUseCase` to validate the entire request before dispatch.

---

## Decision Outcome

Chosen Option: **Option 3: Composite Pre-Flight Contract Modeling in `ed-schema`**.

### 1. The Three Cardinal Header Categories

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                HTTP Header Classification                              │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│   1. Protocol & Format     │   2. Client Identity & Auth │   3. Transport & State      │
│   (Static Contract)        │   (Injected Contract)       │   (Dynamic Operational)     │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ • Content-Type             │ • Authorization (Bearer)    │ • Cookie / Session ID       │
│ • Accept                   │ • X-API-Key                 │ • If-None-Match (ETag)      │
│ • Content-Encoding (gzip)  │ • User-Agent                │ • X-RateLimit-* (Response)  │
│ • Accept-Language          │ • Custom Tenant / Client ID │ • Retry-After (Response)    │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

1. **Protocol & Content Negotiation (Static Contract):** Invariant per endpoint, declared at schema definition time (e.g. `Content-Type: application/json`).
2. **Client Identity & Authentication (Injected Contract):** Structural shape and pattern defined in schema (e.g. requires `Authorization: Bearer <token>` or `X-API-Key: <key>`), while concrete secret values are resolved at runtime via `ed-transport`'s `CredentialProviderPort`.
3. **Transport & Cache State (Dynamic Operational):** Ephemeral negotiation headers (`ETag`, `If-Modified-Since`, `Retry-After`) evaluated dynamically during HTTP dispatch.

---

### 2. Core Domain Contracts (`core/domain/`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from ed_schema.core.domain.descriptor import SchemaDescriptor


class HeaderRequirement(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    COMPUTED = "computed"  # e.g., Content-Length, digests


@dataclass(frozen=True)
class HeaderParameterContract:
    """Represents a single HTTP header boundary rule."""

    name: str  # Case-insensitive header name
    requirement: HeaderRequirement = HeaderRequirement.REQUIRED
    default_value: str | None = None
    pattern: str | None = None  # Regex, e.g. r'^Bearer [a-zA-Z0-9_\-\.]+$'
    description: str | None = None


@dataclass(frozen=True)
class EndpointContract:
    """Composite boundary contract binding headers, endpoint, and payload schemas."""

    descriptor: SchemaDescriptor
    request_headers: tuple[HeaderParameterContract, ...] = ()
    response_headers: tuple[HeaderParameterContract, ...] = ()
    request_body_schema: str | None = None
    response_body_schema: str | None = None
```

---

### 3. Unified Pre-Flight Validation Interactor

In `src/ed_schema/core/use_cases/validate_endpoint_call.py`:

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    header_errors: tuple[str, ...] = ()
    payload_errors: tuple[str, ...] = ()


class ValidateEndpointCallUseCase:
    """Composite pre-flight validation gate checking headers and payload simultaneously."""

    def __init__(
        self,
        registry: SchemaRegistryPort,
        header_validator: HeaderValidatorPort,
        payload_validator: SchemaValidatorPort,
    ) -> None:
        self._registry = registry
        self._header_validator = header_validator
        self._payload_validator = payload_validator

    def execute(
        self,
        descriptor: SchemaDescriptor,
        headers: dict[str, str],
        payload: dict[str, Any] | None = None,
    ) -> ValidationResult:
        contract = self._registry.get_contract(descriptor)
        if not contract:
            raise SchemaNotFoundError(f"No contract registered for {descriptor}")

        header_errors = self._header_validator.validate(
            headers=headers, contracts=contract.request_headers
        )
        payload_errors = ()
        if payload is not None and contract.request_body_schema:
            payload_errors = self._payload_validator.validate(
                payload=payload, schema_id=contract.request_body_schema
            )

        return ValidationResult(
            is_valid=(len(header_errors) == 0 and len(payload_errors) == 0),
            header_errors=tuple(header_errors),
            payload_errors=tuple(payload_errors),
        )
```

As codified in [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md), consumer applications invoke this use case directly via `SchemaEngine.validate_call(descriptor, headers, payload)`.

---

## Consequences

### Positive Consequences
* **Single Pre-Flight Inspection:** Downstream callers (`ed-connectors`) validate the entire outbound transmission (headers + payload) in one call.
* **Zero Socket Waste:** Malformed requests fail locally in microseconds without making unnecessary outbound network calls.
* **Strict Boundary Decoupling:** `ed-schema` verifies structural format rules; `ed-transport` injects credentials and performs network dispatch.
* **Typed DTO Generation:** Header contracts can compile into typed Python DTOs via `SchemaEngine.compile_models()`.

### Negative Consequences & Mitigations
* **Slightly More Verbose Manifests:** Providers must declare both headers and payload schemas in their contracts.
  * *Mitigation:* Sensible defaults (e.g. automatic `Content-Type: application/json`) minimize boilerplate for standard REST/JSON endpoints.
