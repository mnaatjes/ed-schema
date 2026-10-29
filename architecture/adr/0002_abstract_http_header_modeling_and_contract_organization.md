---
title: "ADR 0002: Abstract HTTP Header Modeling and Contract Organization"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0001 (ed-schema)", "ADR 0035 (ed-telemetry)", "OpenAPI 3.1 Specification"]
informed: ["All Engineers", "Integration Client Authors (ed-capi, ed-inara, ed-eddn, ed-connectors)"]
tags: ["adr", "architecture", "headers", "contracts", "openapi", "hexagonal"]
---

# ADR 0002: Abstract HTTP Header Modeling and Contract Organization

## Context and Problem Statement

HTTP transport requests and responses interact with external API targets (`Frontier CAPI`, `EDDN`, `Inara`, `Spansh`, `EDSM`) through both payload bodies and HTTP headers. Headers govern critical contract boundaries, including authentication schemes, content negotiation, compression, client identification, rate-limiting, and cache validation.

However, unlike JSON bodies, HTTP headers introduce unique structural constraints:
1. **Case-Insensitivity & Multi-Valued Entries:** HTTP headers are case-insensitive keys mapped to string values or comma-delimited token lists.
2. **Variable Lifecycles & Sources:** Headers originate from disparate sources at different phases:
   - Static protocol constants (`Content-Type: application/json`).
   - Client identity configurations (`User-Agent: EDDN-Relay/2.1`).
   - Ephemeral credentials injected per request (`Authorization: Bearer <token>`).
   - Dynamic session state or cookies (AWS `sessionid` cookies).
3. **Dual Contract Roles (Request vs. Response):** Request headers enforce client contract prerequisites; response headers provide caller metadata (`X-RateLimit-Remaining`, `Retry-After`, `ETag`).

Historically, client libraries built ad-hoc header dictionaries right before network dispatch. This led to:
- Missing mandatory headers failing only after opening remote network sockets.
- Secret tokens leaked or improperly formatted.
- Lack of typed dataclasses and static IDE autocompletion for headers.
- Duplicated header validation logic across client packages.

How should `ed-schema` abstractly model, organize, and validate HTTP header contracts for inheriting packages without leaking domain logic or conflating transport dispatch responsibilities?

---

## Decision Drivers

* **First-Class Contract Parity:** Headers must be treated with the same contractual rigor as JSON bodies, including validation, schema documentation, and type generation.
* **OpenAPI 3.1 Structural Alignment:** Align header modeling with industry-standard OpenAPI 3.1 parameter contracts (`in: header`).
* **Pre-Flight Validation:** Missing or malformed headers must fail fast locally before engaging network sockets in `ed-transport`.
* **Zero Secret Storage:** `ed-schema` models the *structure* and *format constraints* (e.g., regex patterns) of headers, but never stores credentials or secret values.
* **Build-Time DTO Generation:** Header contracts must compile into immutable, statically typed Python dataclasses to eliminate stringly typed dictionary mistakes.

---

## Considered Options

* **Option 1: Ad-Hoc Dictionary Construction in Client Packages.** Leave header assembly entirely to downstream client libraries as untyped `dict[str, str]`.
  *(Rejected: High error rate, no schema validation, zero static typing, and frequent runtime network failures due to missing required headers).*
* **Option 2: Transport-Layer Header Injection Only (`ed-transport`).** Force all header management into `ed-transport`.
  *(Rejected: Violates single-responsibility; `ed-transport` is a physical network engine, not a contract schema registry. It lacks context on which specific headers are required by individual API endpoints).*
* **Option 3: Abstract Header Contract Domain Model in `ed-schema`.** Formally model header rules as part of composite `EndpointContract` definitions, categorize headers into three cardinal architectural classes, generate typed Python DTOs at build time, and provide pre-flight validation.

---

## Decision Outcome

Chosen Option: **Option 3: Abstract Header Contract Domain Model in `ed-schema`**.

### 1. The Three Cardinal Header Categories

To maintain business-logic ignorance, `ed-schema` classifies all HTTP headers into three orthogonal architectural categories:

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
2. **Client Identity & Authentication (Injected Contract):** Structural shape and pattern are defined in the schema (e.g. requires `Authorization: Bearer <token>` or `X-API-Key: <key>`), while concrete secret values are resolved at runtime via `ed-transport`'s `CredentialProviderPort`.
3. **Transport & Cache State (Dynamic Operational):** Ephemeral negotiation headers (`ETag`, `If-Modified-Since`, `Retry-After`) evaluated dynamically during HTTP dispatch.

---

### 2. Domain Entities in `ed-schema/core/domain/`

`ed-schema` introduces pure domain entities capturing header parameters and composite endpoint contracts:

```python
from dataclasses import dataclass, field
from enum import Enum


class HeaderRequirement(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    COMPUTED = "computed"  # e.g., Content-Length, digests


@dataclass(frozen=True)
class HeaderParameterContract:
    """Represents a single HTTP header boundary rule."""

    name: str  # Case-insensitive header name (e.g., 'Authorization', 'Content-Type')
    requirement: HeaderRequirement = HeaderRequirement.REQUIRED
    default_value: str | None = None  # e.g., 'application/json'
    pattern: str | None = None  # Validation regex, e.g. r'^Bearer [a-zA-Z0-9_\-\.]+$'
    description: str | None = None


@dataclass(frozen=True)
class EndpointContract:
    """Composite boundary contract binding headers, endpoint descriptor, and payload schemas."""

    descriptor: SchemaDescriptor
    request_headers: tuple[HeaderParameterContract, ...] = ()
    response_headers: tuple[HeaderParameterContract, ...] = ()
    request_body_schema: str | None = None  # Pointer to JSON Schema file
    response_body_schema: str | None = None
```

---

### 3. Inheriting Package Lifecycle: Declaration, Compilation, and Execution

Downstream libraries (`ed-capi`, `ed-inara`, `ed-eddn`) consume this model through three decoupled lifecycle phases:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Declaration Phase (Developer Machine / Schema Definitions)          │
│    Inheriting packages declare endpoints & headers in JSON or YAML.    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ CLI Code Generation
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Compile Phase (ed-schema generate-models)                           │
│    Compiles typed Header DTOs into Python source files.                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct Import
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Execution Phase (Runtime)                                           │
│    • Client instantiates typed Header DTO.                             │
│    • Pre-flight validation via ed-schema validates patterns & keys.   │
│    • Validated header map dispatched via ed-transport.                │
└────────────────────────────────────────────────────────────────────────┘
```

#### Phase 1: Declaration Phase (Schema Definition)
Inheriting packages declare endpoint headers in their local `schemas/` directory:
```json
{
  "endpoint": "/inapi/v1/",
  "headers": {
    "Content-Type": { "requirement": "required", "default": "application/json" },
    "Accept": { "requirement": "required", "default": "application/json" }
  }
}
```

#### Phase 2: Compile Phase (`ed-schema` CLI)
The `ed-schema generate-models` command inspects header declarations and emits typed, frozen Python dataclasses committed into the client repository:
```python
@dataclass(frozen=True)
class InaraRequestHeaders:
    content_type: str = "application/json"
    accept: str = "application/json"
```

#### Phase 3: Execution & Validation Phase (Runtime)
1. **Pre-Flight Validation:** The client passes its assembled headers into `ed-schema`'s `validate_headers(descriptor, headers_dict)`. If a required header is absent or violates its regex pattern, a `HeaderValidationError` is raised locally without dispatching network calls.
2. **Transport Dispatch:** The validated header dictionary is supplied directly to `ed-transport`'s `HttpRequest` DTO for physical execution.

---

## Consequences

### Positive Consequences
* **Fail-Fast Local Validation:** Contract violations (missing headers, invalid auth formats) fail locally before network requests are dispatched.
* **Full Static Typing:** Generated header DTOs prevent typo errors, casing bugs, and provide native IDE autocompletion.
* **Separation of Concerns:** `ed-schema` defines and validates the contract shape; `ed-transport` performs physical dispatch and secret injection.
* **OpenAPI 3.1 Interoperability:** Clean mapping to and from standard OpenAPI `in: header` parameter objects.

### Negative Consequences & Mitigations
* **Additional Schema Modeling Overhead:** Endpoints require explicit header contract definitions.
  * *Mitigation:* Sensible defaults (e.g. automatic `Content-Type: application/json` inference) minimize boilerplate for standard REST/JSON endpoints.
