---
title: "ADR 0006: Programmatic Driving Adapter Facade Definition (SchemaEngine)"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0001 (ed-schema)", "ADR 0002 (ed-schema)", "ADR 0003 (ed-schema)", "ADR 0004 (ed-schema)", "ADR 0005 (ed-schema)", "ed-transport ADR 0002"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors, ed-telemetry)"]
tags: ["adr", "architecture", "facade", "driving-adapter", "ergonomics", "hexagonal"]
---

# ADR 0006: Programmatic Driving Adapter Facade Definition (SchemaEngine)

## Context and Problem Statement

`ed-schema` provides five distinct core capabilities formalized across ADRs 0001 through 0005:
1. **ADR 0001:** Multi-namespace manifest loading and 4-tuple composite key indexing (`CompositeSchemaRegistry`).
2. **ADR 0002:** In-process build-time Python dataclass compilation (`GenerateDataclassesUseCase`).
3. **ADR 0003:** Granular in-process AST schema parity verification (`VerifyParityUseCase`).
4. **ADR 0004:** Strict wire DTO naming conventions and lexical scoping formulas.
5. **ADR 0005:** Composite pre-flight endpoint and HTTP header contract validation (`ValidateEndpointCallUseCase`).

In Hexagonal Architecture, internal use cases, domain registries, and ports must remain decoupled from consumer ergonomics. If consuming libraries (`ed-connectors`) must manually construct dependency injection containers, resolve individual use cases, and coordinate registry instances:
- Consumer setup boilerplate proliferates.
- Refactoring internal port signatures causes breaking API changes across the fleet.
- Incorrect lifecycle management risks sharing non-thread-safe state across worker threads.

How should `ed-schema` structure its primary **Driving Adapter Facade** to expose an ergonomic, unified, in-process programmatic Python API for downstream libraries?

---

## Decision Drivers

* **Single Cohesive Client Facade:** A single entrypoint (`from ed_schema import SchemaEngine`) providing intuitive access to compilation, verification, registration, and pre-flight validation.
* **Pure In-Process Library Contract:** Zero reliance on shell CLI commands or external process spawns.
* **Encapsulated Dependency Injection:** The facade must manage its internal container (`Container`) transparently while allowing optional inversion-of-control overrides for testing.
* **Immutable Result Types:** Methods must return strongly typed, immutable dataclasses (`ParityReport`, `ValidationResult`, `list[Path]`).
* **Microsecond In-Memory Latency:** Runtime lookup and pre-flight validation methods must execute in microseconds to support real-time game telemetry streams.

---

## Considered Options

* **Option 1: Direct Consumer Injection.** Require consumers to instantiate `Container()`, manually wire ports, and call use cases directly.
  *(Rejected: Excessive boilerplate; exposes internal hexagonal wiring to consumer code).*
* **Option 2: Standalone Modules & Functions.** Export loose top-level functions (`compile_models()`, `verify_parity()`, `validate_call()`).
  *(Rejected: Makes lifecycle and registry state management awkward; prevents dependency injection or mocking in tests).*
* **Option 3: Unified Programmatic Driving Facade (`SchemaEngine`).** Encapsulate container wiring, registries, and interactors behind a thread-safe, stateful facade class.

---

## Decision Outcome

Chosen Option: **Option 3: Unified Programmatic Driving Facade (`SchemaEngine`)**.

### 1. Architectural Role of `SchemaEngine`

`SchemaEngine` is the canonical driving adapter residing in `src/ed_schema/adapters/driving/facade.py` and exported at the package root `src/ed_schema/__init__.py`. It acts as the orchestrator connecting external callers to internal hexagonal use cases:

```
┌────────────────────────────────────────────────────────────────────────┐
│             External Callers (ed-connectors / scripts / tests)         │
│                                                                        │
│                   from ed_schema import SchemaEngine                   │
│                                │                                       │
│                                ▼                                       │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                      SchemaEngine (Facade)                     │   │
│   │                                                                │   │
│   │  • registry: CompositeSchemaRegistry                           │   │
│   │  • load_manifests(manifests) -> None                           │   │
│   │  • compile_models(schema_dir, output_dir, ...) -> list[Path]   │   │
│   │  • verify_parity(schema_dir, models_dir, ...) -> ParityReport  │   │
│   │  • validate_call(descriptor, headers, payload) -> Result       │   │
│   └──────┬──────────────┬──────────────┬───────────────┬───────────┘   │
└──────────┼──────────────┼──────────────┼───────────────┼───────────────┘
           │              │              │               │
           ▼              ▼              ▼               ▼
    [ADR 0001]     [ADR 0002]     [ADR 0003]      [ADR 0005]
    Registry       GenerateModels  VerifyParity    ValidateEndpoint
    Storage SPI    Codegen SPI    AST Matcher     Header Validator
```

---

### 2. Complete Public Interface Specification

```python
from pathlib import Path
from typing import Any, Sequence
from ed_schema.bootstrap.container import Container
from ed_schema.core.domain.contract import EndpointContract
from ed_schema.core.domain.descriptor import SchemaDescriptor
from ed_schema.core.domain.parity import ParityReport
from ed_schema.core.domain.registry import CompositeSchemaRegistry, SchemaKey
from ed_schema.core.domain.validation import ValidationResult
from ed_schema.core.use_cases.generate_dataclasses import (
    GenerateDataclassesUseCase,
)
from ed_schema.core.use_cases.validate_endpoint_call import (
    ValidateEndpointCallUseCase,
)
from ed_schema.core.use_cases.verify_parity import VerifyParityUseCase


class SchemaEngine:
    """Primary programmatic driving facade for ed-schema."""

    def __init__(self, container: Container | None = None) -> None:
        self._container = container or Container()
        self._registry: CompositeSchemaRegistry = self._container.resolve(
            CompositeSchemaRegistry
        )

    # -------------------------------------------------------------------------
    # 1. Registry & Manifest Management (ADR 0001)
    # -------------------------------------------------------------------------
    @property
    def registry(self) -> CompositeSchemaRegistry:
        """Returns the active in-memory composite schema registry."""
        return self._registry

    def load_manifests(self, manifests: Sequence[Any]) -> None:
        """Ingests schemas and endpoint contracts across provider manifests."""
        for manifest in manifests:
            self._registry.load_from_directory(
                namespace=manifest.name,
                directory=Path(manifest.schema_dir),
            )
            for contract in manifest.endpoints:
                self._registry.register_contract(contract)

    # -------------------------------------------------------------------------
    # 2. Build-Time Code Generation (ADR 0002 & ADR 0004)
    # -------------------------------------------------------------------------
    def compile_models(
        self,
        schema_dir: str | Path,
        output_dir: str | Path,
        class_prefix: str = "",
        base_class: str | None = None,
    ) -> list[Path]:
        """Compiles canonical JSON schemas into typed Python dataclasses."""
        use_case: GenerateDataclassesUseCase = self._container.resolve(
            GenerateDataclassesUseCase
        )
        return use_case.execute(
            schema_dir=Path(schema_dir),
            output_dir=Path(output_dir),
            class_prefix=class_prefix,
            base_class=base_class,
        )

    # -------------------------------------------------------------------------
    # 3. In-Process Parity Verification (ADR 0003)
    # -------------------------------------------------------------------------
    def verify_parity(
        self,
        schema_dir: str | Path,
        models_dir: str | Path,
        namespace: str | None = None,
        class_prefix: str = "",
    ) -> ParityReport:
        """Verifies structural AST equivalence between schemas and models."""
        use_case: VerifyParityUseCase = self._container.resolve(
            VerifyParityUseCase
        )
        return use_case.execute(
            schema_dir=Path(schema_dir),
            models_dir=Path(models_dir),
            namespace=namespace,
            class_prefix=class_prefix,
        )

    # -------------------------------------------------------------------------
    # 4. Composite Pre-Flight Validation (ADR 0005)
    # -------------------------------------------------------------------------
    def validate_call(
        self,
        descriptor: SchemaDescriptor,
        headers: dict[str, str],
        payload: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validates outbound headers and payload against registered contracts."""
        use_case: ValidateEndpointCallUseCase = self._container.resolve(
            ValidateEndpointCallUseCase
        )
        return use_case.execute(
            descriptor=descriptor,
            headers=headers,
            payload=payload,
        )
```

---

## Consequences

### Positive Consequences
* **Single Ergonomic API:** Consumers import one class (`from ed_schema import SchemaEngine`) to access all library functionality.
* **Decoupled Internal Refactoring:** Internal use case signatures and port implementations can evolve without breaking the public `SchemaEngine` contract.
* **Testability:** Consuming applications can easily supply a mock `Container` or stub `SchemaEngine` during unit tests.
* **Strict Hexagonal Discipline:** Preserves pure inward dependency direction; `SchemaEngine` is a Driving Adapter, not core domain logic.

### Negative Consequences & Mitigations
* **Slight Facade Indirection:** Calls route through `SchemaEngine` before reaching use cases.
  * *Mitigation:* Negligible nanosecond method invocation overhead.
