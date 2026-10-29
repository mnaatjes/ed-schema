---
title: "ADR 0002: Programmatic Build-Time Dataclass Compilation"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["RFC 0001 (ed-schema)", "ADR 0001 (ed-schema)", "PEP 561"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "codegen", "build-time", "dataclasses", "hexagonal"]
---

# ADR 0002: Programmatic Build-Time Dataclass Compilation

## Context and Problem Statement

Downstream integration libraries (`ed-connectors`) require Python data models to serialize and deserialize wire payloads when communicating with remote APIs. In Python architectures, model generation typically falls into two camps:
1. **Dynamic Runtime Evaluation:** Inspecting JSON Schemas or OpenAPI contracts at application startup and dynamically fabricating classes via `type()`, `eval()`, or runtime model factories.
2. **Build-Time Compilation:** Compiling schemas into static Python source code (`.py`) during development or pre-commit, committing the generated files to git, and shipping them in the package wheel.

Dynamic runtime code generation creates catastrophic anti-patterns:
- **No IDE Autocomplete:** Editors and language servers (PyLance, PyCharm) cannot inspect dynamically generated classes.
- **Broken Static Analysis:** Type checkers (`mypy`, `pyright`) fail on dynamic types, destroying type safety across the fleet.
- **Latency & Startup Penalty:** Parsing dozens of JSON schemas at startup degrades application launch times on resource-constrained devices (Steam Deck / Proton).
- **Subprocess Shell Leaks:** Spawning terminal CLI tools (`subprocess.run(["ed-schema", ...])`) from within a pure library violates in-process library isolation.

How should `ed-schema` provide reliable, deterministic Python dataclass generation while strictly remaining a **pure in-process library package**?

---

## Decision Drivers

* **Pure Library Packaging (In-Process Execution):** `ed-schema` must operate entirely within the caller's Python interpreter without spawning shell CLI commands or external executables.
* **Build-Time Pre-Commit Invariant:** Generated Python dataclasses must be committed to git as permanent source files. Zero dynamic code generation at application runtime.
* **Targeted Subpackage Output:** Ability to compile schemas for a specific provider directory (e.g. `src/ed_connectors/adapters/driven/providers/inara/schemas/` $\rightarrow$ `.../models/`).
* **High Performance Dataclasses:** Generated models must leverage standard library `@dataclass(frozen=True)` or high-performance equivalents (`msgspec`) with full PEP 484/585 typing.
* **Separation of Concerns:** Codegen compiler engines (`datamodel-code-generator`) must live behind a driven hexagonal SPI port (`CodeGeneratorPort`).

---

## Considered Options

* **Option 1: Runtime Dynamic Dataclass Generation (`type()` / `eval()`).** Evaluate schemas dynamically on demand in memory.
  *(Rejected: Destroys static type checking, removes IDE autocomplete, and degrades startup performance).*
* **Option 2: Standalone CLI Executable.** Ship `ed-schema` as a terminal executable called via shell scripts (`ed-schema generate-models`).
  *(Rejected: Violates the library package boundary; introduces subprocess overhead and external execution dependencies).*
* **Option 3: Programmatic Library Interactor (`SchemaEngine.compile_models()`).** Provide a pure programmatic facade wrapping `GenerateDataclassesUseCase` and a driven `CodeGeneratorPort`. Downstream packages invoke this in-process via developer build scripts (`scripts/compile_models.py`).

---

## Decision Outcome

Chosen Option: **Option 3: Programmatic Library Interactor (`SchemaEngine.compile_models()`)**.

### 1. Build-Time Compilation Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│              Developer Machine / Build Pipeline (ed-connectors)        │
│                                                                        │
│   schemas/inara/*.json                                                 │
│          │                                                             │
│          ▼ (Direct Python In-Process Call)                             │
│   SchemaEngine.compile_models(                                         │
│       schema_dir=".../providers/inara/schemas",                       │
│       output_dir=".../providers/inara/models",                        │
│       class_prefix="Inara"                                            │
│   )                                                                    │
│          │                                                             │
│          ▼ Emits Static Source Code                                    │
│   models/inara/*.py (Committed to Git & Packaged in Wheel)             │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Hexagonal Port and Facade Architecture

1. **Driving Facade (`SchemaEngine`):**
   Exposed via `adapters/driving/facade.py` as codified in [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md). Downstream packages call `SchemaEngine.compile_models()` in-process without spawning external shell processes.

2. **Driven SPI (`CodeGeneratorPort`):**
   Defined in `core/ports/driven/code_generator_port.py`, shielding the core from third-party compiler dependencies (`datamodel-code-generator` / `jinja2`).

3. **Downstream Usage (`scripts/compile_models.py`):**
   As formalized in [ADR 0007](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0007_consumer_build_pipeline_and_parity_test_harness_patterns.md), consuming repositories execute model compilation via a standardized script invoking `SchemaEngine`:
   ```python
   from ed_schema import SchemaEngine

   engine = SchemaEngine()
   engine.compile_models(
       schema_dir="src/ed_connectors/providers/capi/schemas",
       output_dir="src/ed_connectors/providers/capi/models",
       class_prefix="Capi",
   )
   ```

---

## Consequences

### Positive Consequences
* **100% Static Type Safety:** All generated models are native Python source files verified by `mypy` and fully autocompleted by IDE language servers.
* **Zero Runtime Overhead:** Downstream applications import models natively via standard Python imports (`from ed_connectors.providers.inara.models import InaraProfileDTO`).
* **In-Process Simplicity:** Eliminates shell subprocess execution, exit code parsing, and path serialization hurdles.
* **Hexagonal Decoupling:** Third-party compiler tools are isolated in `adapters/driven/codegen/`.

### Negative Consequences & Mitigations
* **Heavier Development Dependencies:** Incorporates `datamodel-code-generator` into the development environment.
  * *Mitigation:* Packaged as an optional extra or build-time dependency (`ed-schema[codegen]`) so pure runtime consumers do not pull unused compilers.
