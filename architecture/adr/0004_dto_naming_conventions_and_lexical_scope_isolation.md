---
title: "ADR 0004: DTO Naming Conventions and Lexical Scope Isolation"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["RFC 0001 (ed-schema)", "ADR 0001 (ed-schema)", "PEP 8", "PEP 561"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "dto", "naming", "pep8", "pep561", "hexagonal"]
---

# ADR 0004: DTO Naming Conventions and Lexical Scope Isolation

## Context and Problem Statement

In a unified fleet architecture (`ed-connectors`), multiple provider subpackages (`capi`, `eddn`, `inara`, `spansh`) interact with overlapping functional concepts:
- Frontier CAPI exposes `/profile` $\rightarrow$ commander profile JSON.
- Inara exposes `getCommanderProfile` $\rightarrow$ commander profile JSON.
- Frontier CAPI exposes `/market` $\rightarrow$ commodity market JSON.
- EDDN exposes `commodity/3` $\rightarrow$ commodity market relay JSON.

If schema code generators compile class names naively from schema titles (e.g. `class Profile:` or `class Market:`), two critical architectural problems arise:
1. **Type Collision & Namespace Ambiguity:** Downstream callers importing multiple modules suffer from ambiguous, colliding class names.
2. **Conflation with Game Domain Entities:** Calling a wire payload `class Ship:` or `class Commander:` blurs the boundary with rich game models (planned `ed-models`), tricking developers into adding business logic, physics, or methods to raw wire serialization DTOs.

How should `ed-schema` govern class naming conventions and lexical scoping to guarantee collision-free type generation and preserve the boundary between wire DTOs and game domain entities?

---

## Decision Drivers

* **PEP 8 PascalCase Class Naming:** Class names must strictly adhere to standard Python capitalization conventions (`PascalCase`).
* **Explicit Wire DTO Demarcation:** Generated classes must be unambiguously marked as wire serialization containers (e.g., `*DTO` or `*Payload`), never bare domain entity names.
* **Namespace / Provider Prefix Scoping:** Generated classes must incorporate deterministic provider prefixes (`CapiProfileDTO`, `InaraProfileDTO`) to avoid global name collisions.
* **PEP 561 Inline Typing Support:** Generated modules must ship with typed attributes and `py.typed` marker compatibility for strict MyPy validation.
* **Zero Domain Logic Invariant:** Generated models are strictly immutable structural containers (`@dataclass(frozen=True)`). Zero helper methods, game physics, or business logic allowed.

---

## Considered Options

* **Option 1: Unadorned Schema Titles.** Generate class names directly from the schema `$id` or `title` property (e.g. `class Profile:`).
  *(Rejected: Causes widespread naming collisions across providers and blurs wire DTOs with game models).*
* **Option 2: Deeply Nested Submodule Imports Only.** Rely solely on package paths without class name prefixes (`from ed_connectors.providers.capi.models.profile import Profile`).
  *(Rejected: Fragile in consuming code; IDE auto-imports frequently select the wrong `Profile` class and create confusing diffs).*
* **Option 3: Deterministic Provider Prefixing and Explicit DTO Suffixing.** Enforce a strict naming formula: `<ProviderPrefix><DescriptorName><DTO|Payload>`.

---

## Decision Outcome

Chosen Option: **Option 3: Deterministic Provider Prefixing and Explicit DTO Suffixing**.

### 1. The DTO vs. Game Domain Model Boundary

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Model Layer Separation                                 │
├─────────────────────────────────────────────┬──────────────────────────────────────────┤
│   Wire DTOs (compiled by ed-schema)         │   Game Domain Models (planned ed-models) │
├─────────────────────────────────────────────┼──────────────────────────────────────────┤
│ • Examples: CapiProfileDTO, InaraEventDTO   │ • Examples: StarSystem, ShipLoadout      │
│ • Pure structural wire containers.          │ • Rich domain behavior & game semantics. │
│ • 100% mirrors remote API JSON fields.      │ • Normalized, clean application model.   │
│ • Frozen dataclass with primitive typing.   │ • Independent of external API formats.   │
└─────────────────────────────────────────────┴──────────────────────────────────────────┘
```

### 2. Naming Formula and Generation Specification

The code generator engine (`adapters/driven/codegen/`) enforces the following template:

$$\text{Class Name} = \text{PascalCase}(\text{ProviderPrefix}) + \text{PascalCase}(\text{SchemaTitle}) + \text{"DTO"}$$

#### Concrete Fleet Examples

| Target API | Schema Source File | Generated Python Class Name | Target Subpackage Path |
| :--- | :--- | :--- | :--- |
| **Frontier CAPI** | `capi/schemas/profile.json` | `CapiProfileResponseDTO` | `ed_connectors.providers.capi.models.profile` |
| **Frontier CAPI** | `capi/schemas/market.json` | `CapiMarketResponseDTO` | `ed_connectors.providers.capi.models.market` |
| **Inara API** | `inara/schemas/envelope.json` | `InaraBatchEnvelopeDTO` | `ed_connectors.providers.inara.models.envelope` |
| **Inara API** | `inara/schemas/getCommanderProfile.json` | `InaraProfileEventDataDTO` | `ed_connectors.providers.inara.models.events` |
| **EDDN Gateway** | `eddn/schemas/journal.json` | `EDDNJournalPayloadDTO` | `ed_connectors.providers.eddn.models.journal` |
| **EDDN Gateway** | `eddn/schemas/commodity.json` | `EDDNCommodityPayloadDTO` | `ed_connectors.providers.eddn.models.commodity` |
| **Spansh API** | `spansh/schemas/systems.json` | `SpanshSystemsResponseDTO` | `ed_connectors.providers.spansh.models.systems` |

### 3. Generated Code Characteristics (PEP 561 & PEP 8)

All generated DTO files adhere to:
```python
# Generated by ed-schema. DO NOT EDIT DIRECTLY.
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InaraProfileEventDataDTO:
    """Wire representation expected by Inara getCommanderProfile event."""

    searchName: str
    searchFrontierID: str | None = None


__all__ = ["InaraProfileEventDataDTO"]
```

---

## Consequences

### Positive Consequences
* **Zero Name Collisions:** Consumers can import `CapiProfileResponseDTO` and `InaraProfileEventDataDTO` into the same file without alias renaming (`import ... as ...`).
* **Unmistakable Architectural Role:** The explicit `*DTO` suffix prevents developers from mistaking wire payloads for normalized game models.
* **Strict Type Safety:** Downstream type checkers (`mypy`) receive full static validation across all fields and optional values.
* **PEP Compliance:** Meets PEP 8, PEP 484, PEP 561, and PEP 585 standards.

### Negative Consequences & Mitigations
* **Longer Class Identifiers:** Class names are slightly more verbose than bare names like `Profile`.
  * *Mitigation:* Modern IDE autocomplete completely mitigates typing friction, and readability is significantly enhanced.
