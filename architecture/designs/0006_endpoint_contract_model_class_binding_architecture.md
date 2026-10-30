---
title: "SDD-006: EndpointContract Model Class Binding Architecture"
status: "draft"
authors: ["@mnaatjes"]
reviewers: ["Core Architecture Team"]
created_at: "2026-10-30"
last_updated_at: "2026-10-30"
related_adrs: [
  "architecture/adr/0001_multi_namespace_manifest_loading_and_composite_schema_registry.md",
  "architecture/adr/0004_dto_naming_conventions_and_lexical_scope_isolation.md",
  "architecture/adr/0006_programmatic_driving_adapter_facade_definition.md",
  "architecture/adr/0009_endpoint_contract_model_class_binding.md"
]
related_rfcs: [
  "architecture/rfcs/0001_fleet_unification_and_provider_subpackage_architecture.md"
]
tags: ["sdd", "designs", "architecture", "binding", "contracts", "models"]
---

# SDD-006: EndpointContract Model Class Binding Architecture

## 1. Introduction and Architectural Motivation

### 1.1 Scope and Objective
This Software Design Document (SDD) defines the structural modifications required to bind compiled Python dataclass types (`model_cls`) directly through provider manifests into the `CompositeSchemaRegistry` via `EndpointContract` and `RegisterSchemaUseCase`.

### 1.2 Problem Context
`SchemaDescriptor` supports an optional `model_cls: type | None = None` attribute to hold the runtime class reference of the compiled Python dataclass. However, because `EndpointContract` in `ed_schema.core.domain.models` omitted `model_cls`, manifests had no mechanism to pass the class reference during registration.

### 1.3 Target Architecture
Updating `EndpointContract` to declare `model_cls: type | None = None` and modifying `RegisterSchemaUseCase.execute()` to pass `model_cls=endpoint.model_cls` ensures that whenever an endpoint specifies a compiled DTO class, any caller resolving the descriptor via `SchemaEngine.resolve_descriptor(key)` obtains both the JSON schema definition and the compiled Python model class in a single $O(1)$ lookup.

---

## 2. Detailed Design

### 2.1 Domain Model Update (`src/ed_schema/core/domain/models.py`)

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

    def __post_init__(self) -> None:
        if not self.route or not self.route.startswith("/"):
            raise DomainValidationError(
                f"EndpointContract 'route' must start with '/': {self.route}"
            )
        if not self.schema_file or not self.schema_file.endswith(".json"):
            raise DomainValidationError(
                f"EndpointContract 'schema_file' must end with '.json': {self.schema_file}"
            )
        if self.model_cls is not None and not isinstance(self.model_cls, type):
            raise DomainValidationError(
                f"EndpointContract 'model_cls' must be a type or None, got: {type(self.model_cls).__name__}"
            )
```

### 2.2 Use Case Update (`src/ed_schema/core/use_cases/register_schema_use_case.py`)

In `RegisterSchemaUseCase.execute()`:
```python
descriptor = SchemaDescriptor(
    key=key,
    schema_definition=schema_def,
    model_cls=endpoint.model_cls,
    header_contract=endpoint.header_contract,
)
self.register(descriptor)
```

---

## 3. Verification Strategy

1. **Domain Unit Tests (`tests/unit/core/test_domain_models.py`):**
   - Validating `EndpointContract` with `model_cls=None`.
   - Validating `EndpointContract` with a valid dataclass type.
   - Asserting `DomainValidationError` if `model_cls` is not a type (e.g. an instance or string).
2. **Use Case Unit Tests (`tests/unit/core/use_cases/test_register_schema_use_case.py`):**
   - Ingesting an `EndpointContract` with `model_cls` populates `SchemaDescriptor.model_cls`.
3. **Integration Tests (`tests/integration/test_schema_engine_e2e.py`):**
   - End-to-end manifest registration with `model_cls` and resolving it from `SchemaEngine`.
