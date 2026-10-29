---
title: "Use-Case Specification: UC-03 Verify Schema Parity"
use_case_id: "UC-03"
status: "approved"
version: "1.0.0"
level: "sea_level"
primary_actor: "Test Runner / Pre-Commit Hook (pytest, pre-commit)"
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
tags: ["use-case", "requirements", "parity", "verification", "ast", "testing", "ci"]
---

# Use-Case Specification: UC-03 Verify Schema Parity

## 1. System Boundary and Scope

```text
+-----------------------------------------------------------------------------------+
| System Boundary: ed-schema (In-Process AST Parity Engine)                          |
|                                                                                   |
|  [Actor: Pytest / Pre-Commit Hook]                                                |
|       |                                                                           |
|       | 1. verify_parity(schema_dir, models_dir, namespace, class_prefix)          |
|       v                                                                           |
|  +--------------------+    +---------------------+    +------------------------+  |
|  | Schema AST Compiler| -> | On-Disk Model Parser| -> | Structural AST Matcher |  |
|  +--------------------+    +---------------------+    +------------------------+  |
|                                                                    |              |
|                                                                    v              |
|                                                        [ParityReport / Exception] |
|                                                        (is_synchronized: True)    |
+-----------------------------------------------------------------------------------+
```

### 1.1 In-Scope
* Pure in-process verification comparing on-disk JSON schemas against compiled Python dataclasses.
* AST-level equivalence matching (structural node comparison via Python's standard `ast` module) that ignores superficial whitespace and formatting differences.
* Granular namespace and path scoping (e.g. verifying only the modified `inara` subpackage during development).
* Returning a structured `ParityReport` or raising `SchemaParityError` with actionable AST diffs.

### 1.2 Out-of-Scope
* **Automatic File Overwriting:** Does not silently modify or regenerate files during verification (compilation is strictly owned by UC-02).
* **Terminal Shell Invocation:** Zero reliance on standalone CLI commands or exit code scraping.

---

## 2. Actors and Stakeholders

* **Primary Actor:** Test Framework (`pytest tests/architecture/test_schema_parity.py`) or Git Pre-Commit Hook (`.pre-commit-config.yaml`).
* **Stakeholder (Release Engineer / Maintainer):** Guarantees zero silent contract drift between JSON schemas and Python models in remote pull requests and production releases.

---

## 3. Pre-conditions and Post-conditions

### 3.1 Pre-conditions
1. Stored schema files exist under `schema_dir`.
2. Target Python model files exist under `models_dir`.
3. The test suite executes in-process within the Python virtual environment.

### 3.2 Post-conditions
1. **Success:** Returns a `ParityReport(is_synchronized=True)` confirming absolute structural synchronization between schemas and models.
2. **Failure:** Raises `SchemaParityError` containing an actionable AST diff detailing missing attributes, mismatched field types, or out-of-sync class definitions.

---

## 4. Main Success Scenario (Basic Flow)

1. The test runner invokes `SchemaEngine.verify_parity(schema_dir, models_dir, namespace, class_prefix)`.
2. `SchemaEngine` delegates to `VerifyParityUseCase`.
3. The use case reads the canonical `.json` schemas from `schema_dir`.
4. The use case compiles an ephemeral in-memory AST of the expected Python dataclasses using the specified `class_prefix`.
5. The use case reads the existing on-disk `.py` models from `models_dir` and parses their AST using `ast.parse()`.
6. The AST matcher walks both trees, comparing class names, field names, type annotations, and default values.
7. Both AST representations match structurally.
8. The use case returns `ParityReport(is_synchronized=True, diff_summary=None)`.
9. The unit test asserts `report.is_synchronized` and passes in under 100 milliseconds.

---

## 5. Alternative and Failure Flows (Extensions)

* **7a. Structural AST Drift Detected (Schema Modified Without Codegen):**
  1. A property was added or modified in the `.json` schema, but the on-disk `.py` dataclass lacks the updated attribute.
  2. The AST matcher records a structural discrepancy.
  3. The use case constructs a detailed diff summary: `Attribute 'credit_balance' expected in 'CapiProfileResponseDTO' but not found on disk`.
  4. The use case raises `SchemaParityError(diff_summary)`.
  5. The test runner catches the error and fails the test or blocks the pre-commit hook with instructions to run `scripts/compile_models.py`.

* **7b. Model File Missing from Disk:**
  1. A schema file exists with no corresponding generated `.py` file in `models_dir`.
  2. The use case raises `MissingModelFileError(schema_file, expected_model_path)`.

---

## 6. Traceability and Mitigations

* **Mitigates:** [RISK-01](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-10](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md).
* **Governing Decisions:** [ADR 0003](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0003_granular_in_process_parity_verification.md), [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md), [ADR 0007](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0007_consumer_build_pipeline_and_parity_test_harness_patterns.md).
