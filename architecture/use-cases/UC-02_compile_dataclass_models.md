---
title: "Use-Case Specification: UC-02 Compile Dataclass Models"
use_case_id: "UC-02"
status: "approved"
version: "1.0.0"
level: "sea_level"
primary_actor: "Developer / Build Pipeline (scripts/compile_models.py)"
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
tags: ["use-case", "requirements", "codegen", "build-time", "dataclasses", "pep8", "pep561"]
---

# Use-Case Specification: UC-02 Compile Dataclass Models

## 1. System Boundary and Scope

```text
+-----------------------------------------------------------------------------------+
| System Boundary: ed-schema (Code Generation & Dataclass Compilation Core)          |
|                                                                                   |
|  [Actor: Developer / Build Script]                                                |
|       |                                                                           |
|       | 1. compile_models(schema_dir, output_dir, class_prefix)                   |
|       v                                                                           |
|  +--------------------+    +---------------------+    +------------------------+  |
|  | Schema Parser Port | -> | Naming & Scope Rule | -> | Driven Codegen SPI     |  |
|  +--------------------+    +---------------------+    +------------------------+  |
|                                                                    |              |
|                                                                    v              |
|                                                        [Compiled Python Files]    |
|                                                        (*.py in provider models/) |
+-----------------------------------------------------------------------------------+
```

### 1.1 In-Scope
* Pure in-process compilation of on-disk JSON Schema files into high-performance, frozen Python dataclasses.
* Generation directed strictly to designated provider subpackage model directories (`src/ed_connectors/providers/<target>/models/`).
* Enforcement of the deterministic PascalCase naming formula: `<ProviderPrefix><SchemaTitle>DTO`.
* Emitting PEP 8 and PEP 561 compliant code with full type annotations and `__all__` exports.
* Overwriting existing generated files idempotently without modifying non-generated companion code.

### 1.2 Out-of-Scope
* **Runtime Dynamic Evaluation:** Zero execution of `eval()`, `exec()`, or dynamic `type()` at application runtime.
* **Terminal Shell Invocation:** Zero spawning of CLI subprocesses (`subprocess.run(["ed-schema", ...])`).
* **Game Model Generation:** Does not generate game domain entities (owned by `ed-models`).

---

## 2. Actors and Stakeholders

* **Primary Actor:** Software Engineer or Local Build Script (`scripts/compile_models.py`).
* **Stakeholder (Developer / IDE):** Demands 100% static type checking with MyPy, rich IDE autocompletion, zero name collisions between providers, and zero application launch latency penalties.

---

## 3. Pre-conditions and Post-conditions

### 3.1 Pre-conditions
1. The target schema directory contains valid Draft-07 or Draft 2020-12 `.json` schema files.
2. The output directory path is writable on the local filesystem.
3. The calling script executes in-process within the Python environment.

### 3.2 Post-conditions
1. **Success:** Static `.py` files containing typed frozen dataclasses are written to the target output directory and formatted according to PEP 8 standards.
2. **Failure:** If schema compilation encounters unresolvable references or invalid syntax, compilation halts with a descriptive `CodeGenerationError`, leaving existing valid code intact.

---

## 4. Main Success Scenario (Basic Flow)

1. The developer or build script calls `SchemaEngine.compile_models(schema_dir, output_dir, class_prefix)`.
2. `SchemaEngine` delegates to `GenerateDataclassesUseCase` with validated `Path` parameters.
3. The use case reads the source schemas from `schema_dir`.
4. The naming rule engine applies the provider prefix to all top-level and nested entity names (`CapiProfileResponseDTO`).
5. The driven `CodeGeneratorPort` adapter (wrapping `datamodel-code-generator`) compiles the schemas into a Python AST.
6. The use case serializes the generated AST to clean Python source code.
7. The source files (`.py`) and an `__init__.py` file are written to `output_dir`.
8. The use case returns a list of created file paths (`list[Path]`) and exits successfully.

---

## 5. Alternative and Failure Flows (Extensions)

* **3a. Schema Contains Unresolvable `$ref` Pointer:**
  1. A schema references an external `$ref` URI that cannot be resolved locally.
  2. `SchemaEngine` raises `SchemaReferenceResolutionError(ref_uri, schema_file)`.
  3. No files are emitted to the output directory.

* **5a. Output Directory Permission Denied:**
  1. The target output directory cannot be created or written to.
  2. `SchemaEngine` raises `OutputDirectoryNotWritableError(output_dir)`.

* **5b. Invalid Class Identifier Generated:**
  1. A schema property or title produces an illegal Python identifier (e.g. contains special symbols or reserved keywords).
  2. The naming engine sanitizes the identifier and appends an explicit field alias mapping.

---

## 6. Traceability and Mitigations

* **Mitigates:** [RISK-02](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-04](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-07](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md).
* **Governing Decisions:** [ADR 0002](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0002_programmatic_build_time_dataclass_compilation.md), [ADR 0004](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0004_dto_naming_conventions_and_lexical_scope_isolation.md), [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md), [ADR 0007](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0007_consumer_build_pipeline_and_parity_test_harness_patterns.md).
