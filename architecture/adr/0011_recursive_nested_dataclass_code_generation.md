---
title: "ADR 0011: Recursive Nested Dataclass Code Generation"
status: "accepted"
date: "2026-10-30"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0002 (ed-schema)", "ADR 0004 (ed-schema)", "ADR 0010 (ed-schema)"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "codegen", "recursive", "dataclasses", "hexagonal"]
---

# ADR 0011: Recursive Nested Dataclass Code Generation

## Context and Problem Statement

`ed-schema` provides programmatic build-time compilation of JSON schemas into typed Python dataclasses via `CompileDataclassesUseCase` and `DatamodelCodeGeneratorAdapter` (`DatamodelGeneratorPort`).

The initial implementation synthesized dataclass code by reading top-level `properties` and mapping `"type": "object"` directly to `dict[str, Any]` and `"type": "array"` to `list[Any]`. When applied to real-world *Elite Dangerous* schemas (such as EDDN `journal-v1.0.json`, CAPI profile schemas, and Inara batch envelopes), this shallow mapping produced DTOs with un-typed dictionary fields:
```python
@dataclass(frozen=True)
class EddnJournalV10DTO:
    schemaRef: str
    header: dict[str, Any]  # Child properties (uploaderID, softwareName) discarded
    message: dict[str, Any]  # Child properties (timestamp, event, StarSystem) discarded
```
This violates the core value proposition of build-time code generation: providing strongly typed, IDE-autocompleted, and `mypy`-verifiable DTOs representing the entire payload structure.

How should `ed-schema` generate recursive, strongly typed dataclasses for nested object properties and object arrays while maintaining clean identifier sanitization and scope isolation?

---

## Decision Drivers

* **Deep Structural Typing:** Every nested object schema (`type: "object"`) with declared `properties` must compile into its own strongly typed frozen dataclass.
* **Topological Definition Order:** Child dataclasses must be defined before parent dataclasses in the generated Python source, or use `from __future__ import annotations`, ensuring zero runtime forward-reference lookup failures.
* **Predictable DTO Naming:** Child dataclasses must inherit clean, contextual PascalCase names (e.g. `EddnJournalV10HeaderDTO`, `EddnJournalV10MessageDTO`) adhering to provider scoping rules (`ADR 0004`).
* **Nested Array Support:** Arrays containing items with `type: "object"` (`items: {"type": "object", "properties": ...}`) must compile to `tuple[ChildDTO, ...]` or `list[ChildDTO]`.
* **Fallback for Dynamic Properties:** Objects explicitly specifying `additionalProperties: true` without declared properties or polymorphic catch-alls must cleanly fall back to `dict[str, Any]`.
* **Zero Runtime Dependencies:** Compiles into native standard library `@dataclass(frozen=True)` without requiring external runtime serialization libraries.

---

## Considered Options

* **Option 1: External `datamodel-code-generator` CLI Subprocess.** Shell out to `datamodel-codegen`.
  *(Rejected: Violates ADR 0002 in-process library constraint and introduces external system binary requirements).*
* **Option 2: Recursive In-Process AST/Code Synthesizer.** Implement a recursive schema visitor in `DatamodelCodeGeneratorAdapter` that traverses object hierarchies, synthesizes discrete child dataclasses for each nested object node, collects them in topological order, and references them in parent type annotations.
  *(Chosen: Pure in-process execution, zero additional runtime dependencies, 100% compliant with ADR 0002/0004/0010).*

---

## Decision Outcome

Chosen Option: **Option 2: Recursive In-Process AST/Code Synthesizer**.

### 1. Recursive Code Generation Algorithm
`DatamodelCodeGeneratorAdapter` traverses the schema definition recursively:
1. `_process_object(schema_dict, class_name)`:
   - Evaluates `properties` and `required` lists.
   - For each property with `type: "object"` and nested `properties`, recursively invokes `_process_object` to produce a child dataclass (e.g., `{parent_class}{PropertyTitle}DTO`).
   - For each property with `type: "array"` where `items.type == "object"` and contains nested `properties`, recursively invokes `_process_object` to produce a child item dataclass (e.g., `{parent_class}{PropertyTitle}ItemDTO`).
   - Maps primitive types (`string` -> `str`, `integer` -> `int`, `number` -> `float`, `boolean` -> `bool`).
   - Orders generated classes so children precede parent classes, exporting all generated classes in `__all__`.

### 2. Identifier Sanitization
All child class names, property attributes, and module filenames use the sanitized rules established in `ADR 0010`:
- Property names sanitized via `sanitize_identifier()`.
- Root and child class names PascalCased via `derive_class_title()`.

### 3. Consequences
* **Positive:** `EddnJournalV10DTO` contains strongly typed `header: EddnJournalV10HeaderDTO` and `message: EddnJournalV10MessageDTO` with full autocomplete and type-checking down to leaf fields (`dto.header.softwareName`, `dto.message.StarSystem`).
* **Positive:** Preserves in-process library isolation without spawning subprocesses or adding heavy external runtime packages.
* **Positive:** Fully deterministic and compatible with AST parity verification (`ADR 0003`).
