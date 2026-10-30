---
title: "ADR 0009: EndpointContract Model Class Binding"
status: "accepted"
date: "2026-10-30"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0001 (ed-schema)", "ADR 0004 (ed-schema)", "ADR 0006 (ed-schema)"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "binding", "contracts", "models", "hexagonal"]
---

# ADR 0009: EndpointContract Model Class Binding

## Context and Problem Statement

`ed-schema` organizes contract metadata through `SchemaDescriptor`, which bundles an endpoint's `SchemaKey`, raw JSON `schema_definition`, optional `header_contract`, and an optional Python dataclass type reference `model_cls: type | None`.

However, during manifest ingestion, provider declarations declare endpoint mappings using `EndpointContract`:
```python
@dataclass(frozen=True)
class EndpointContract:
    route: str
    schema_file: str
    discriminator_field: str | None = None
    discriminator_value: str | None = None
    header_contract: HeaderContract | None = None
```

Because `EndpointContract` lacks a `model_cls` field, manifest authors cannot specify the compiled Python DTO class corresponding to the route. Consequently, when `RegisterSchemaUseCase` ingests manifests, `SchemaDescriptor.model_cls` is consistently initialized to `None`, severing the link between the stored JSON schema and its compiled Python dataclass.

How should `ed-schema` bridge the declarative contract in `EndpointContract` to `SchemaDescriptor.model_cls` without introducing dynamic runtime imports or compromising immutability?

---

## Decision Drivers

* **Closing the Schema-to-DTO Loop:** Enable `SchemaDescriptor` to provide callers with direct access to the compiled Python dataclass type (`model_cls`).
* **Declarative and Explicit:** Avoid brittle runtime string reflection or dynamic `importlib` calls; allow manifest declarations to bind explicit class references.
* **Backward Compatibility:** `model_cls` must remain optional (`None` by default) so manifests can register raw schema definitions even before models are compiled.
* **Hexagonal Purity:** Maintain complete decoupling from specific game domain entities or third-party serialization frameworks.

---

## Considered Options

* **Option 1: Dynamic Runtime Module Reflection.** Omit `model_cls` from `EndpointContract` and attempt to dynamically import models by string convention (e.g. `importlib.import_module(f"...models.{stem}")`) inside `RegisterSchemaUseCase`.
  *(Rejected: Violates library boundary isolation, breaks static analysis with mypy, and fails in environments without identical directory structures).*
* **Option 2: Declarative `model_cls` Binding on `EndpointContract`.** Add `model_cls: type | None = None` directly to `EndpointContract` and forward it to `SchemaDescriptor` during `RegisterSchemaUseCase.execute()`.
  *(Chosen: Explicit, fully type-safe, reflection-free, and immutably preserved).*

---

## Decision Outcome

Chosen Option: **Option 2: Declarative `model_cls` Binding on `EndpointContract`**.

### 1. Structural Model Update

```python
@dataclass(frozen=True)
class EndpointContract:
    """Declares an endpoint mapping within a provider manifest."""

    route: str
    schema_file: str
    discriminator_field: str | None = None
    discriminator_value: str | None = None
    header_contract: HeaderContract | None = None
    model_cls: type | None = None
```

### 2. Ingestion Forwarding

In `RegisterSchemaUseCase.execute()`:
```python
descriptor = SchemaDescriptor(
    key=key,
    schema_definition=schema_def,
    model_cls=endpoint.model_cls,
    header_contract=endpoint.header_contract,
)
```

---

## Consequences

### Positive Consequences
* **Direct Class Resolution:** Consumers calling `engine.resolve_descriptor(key)` can inspect `descriptor.model_cls` and pass it to their preferred deserializer/serializer (e.g. `msgspec`, `cattrs`, or `pydantic`).
* **Zero Runtime Overhead:** Passing a class reference has zero latency and introduces zero disk or reflection I/O.
* **Static Typing:** Fully supported by PEP 484 and `mypy --strict`.

### Negative Consequences & Mitigations
* Manifests that bind `model_cls` must be loaded after or alongside the compiled model modules.
  * *Mitigation:* Because compilation is build-time (`ADR 0002`), compiled `.py` dataclasses are already committed to version control and available at runtime import time.
