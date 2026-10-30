---
title: "SDD-008: Recursive Nested Dataclass Code Generation Architecture"
status: "draft"
authors: ["@mnaatjes"]
reviewers: ["Core Architecture Team"]
created_at: "2026-10-30"
last_updated_at: "2026-10-30"
related_adrs: [
  "architecture/adr/0002_programmatic_build_time_dataclass_compilation.md",
  "architecture/adr/0004_dto_naming_conventions_and_lexical_scope_isolation.md",
  "architecture/adr/0010_codegen_identifier_and_module_filename_sanitization.md",
  "architecture/adr/0011_recursive_nested_dataclass_code_generation.md"
]
related_rfcs: [
  "architecture/rfcs/0001_fleet_unification_and_provider_subpackage_architecture.md"
]
tags: ["sdd", "designs", "architecture", "codegen", "recursive", "dataclasses"]
---

# SDD-008: Recursive Nested Dataclass Code Generation Architecture

## 1. Introduction and Architectural Motivation

### 1.1 Scope and Objective
This Software Design Document (SDD) specifies the architecture and implementation design for deep recursive Python dataclass compilation within `DatamodelCodeGeneratorAdapter` (`src/ed_schema/adapters/driven/codegen/datamodel_code_generator_adapter.py`).

### 1.2 Problem Context
In `ed-schema` v1.0.1, `DatamodelCodeGeneratorAdapter` mapped all properties with `"type": "object"` to `dict[str, Any]`. In schemas like EDDN `journal-v1.0.json`, this discarded typed contracts for `header` (`uploaderID`, `softwareName`, `softwareVersion`, `gameversion`, etc.) and `message` (`timestamp`, `event`, `StarSystem`, `StarPos`, etc.), generating shallow envelope models.

---

## 2. Technical Architecture & Recursive Compiler Specification

### 2.1 Component Structure
`DatamodelCodeGeneratorAdapter` introduces a recursive code synthesis model:

```
┌────────────────────────────────────────────────────────┐
│             DatamodelCodeGeneratorAdapter              │
│                                                        │
│  generate_dataclasses(schema_path, output_file, ...)   │
│         │                                              │
│         ▼                                              │
│  _ClassCollector                                       │
│  ├── collect_object_classes(raw_schema, root_name)     │
│  │   ├── child objects (e.g. Header, Message)          │
│  │   │   └── recursively collects sub-classes         │
│  │   └── array items with object schemas               │
│  │       └── recursively collects item sub-classes     │
│  └── emit_python_module()                              │
│      ├── from __future__ import annotations            │
│      ├── child dataclasses                             │
│      ├── root dataclass                                │
│      └── __all__ = tuple(...)                          │
└────────────────────────────────────────────────────────┘
```

### 2.2 Class Synthesis Model
Each synthesized dataclass definition contains:
1. `class_name`: Formed by `{parent_prefix}{node_title}DTO`.
2. `docstring`: Extracted from the sub-schema's `description`, falling back to `Data transfer object for {node_title}.`
3. `fields`:
   - Required fields first (no default values).
   - Optional fields second with `= None`.
   - Types:
     - Primitives: `str`, `int`, `float`, `bool`.
     - Sub-objects: references child dataclass type (e.g. `EddnJournalV10HeaderDTO`).
     - Arrays of primitives: `list[str]`, `list[int]`, etc.
     - Arrays of sub-objects: `list[EddnJournalV10ItemDTO]`.
     - Generic objects (without defined properties): `dict[str, Any]`.

### 2.3 Topological Sorting & Imports
All generated dataclasses are emitted in topological dependency order (child classes preceding parent classes), and the file opens with:
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
```
All emitted classes are listed in `__all__`.

---

## 3. Test & Verification Plan

### 3.1 Unit Testing (`tests/unit/adapters/driven/test_datamodel_code_generator_adapter.py`)
1. `test_generate_dataclasses_recursive_nested_objects`:
   - Compile a schema with root object containing nested `header` and `message` objects.
   - Assert child classes `CapiProfileHeaderDTO` and `CapiProfileMessageDTO` are generated.
   - Assert parent class `CapiProfileDTO` references `header: CapiProfileHeaderDTO` and `message: CapiProfileMessageDTO`.
   - Assert `ast.parse` validates valid Python syntax.
2. `test_generate_dataclasses_recursive_arrays`:
   - Compile a schema with `items: {"type": "object", "properties": {"id": {"type": "string"}}}`.
   - Assert child item dataclass is generated and referenced as `list[ItemDTO]`.

### 3.2 Parity Verification Compatibility
Ensure `VerifySchemaParityUseCase` checks fields across root classes without regressions.

### 3.3 Quality Gates
Execute `.venv/bin/python scripts/verify.py` to confirm all quality checks pass.
