---
title: "ADR 0010: Code Generation Identifier and Module Filename Sanitization"
status: "accepted"
date: "2026-10-30"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0002 (ed-schema)", "ADR 0004 (ed-schema)", "ADR 0006 (ed-schema)"]
informed: ["All Engineers", "Integration Client Authors"]
tags: ["adr", "architecture", "codegen", "sanitization", "syntax", "python"]
---

# ADR 0010: Code Generation Identifier and Module Filename Sanitization

## Context and Problem Statement

When compiling JSON Schema documents into Python dataclasses via `DatamodelCodeGeneratorAdapter` (`CompileDataclassesUseCase`), two structural defects occur when processing upstream industry schemas (such as EDDN Draft-04/07 schemas):

1. **Invalid Python Field Identifiers:** Standard JSON schemas frequently use non-Python characters in property names, most notably the leading dollar sign (`$`) in envelope metadata fields like `$schemaRef`, `$id`, or `$schema`. `DatamodelCodeGeneratorAdapter` previously sanitized field names using:
   ```python
   clean_field = p if p.isidentifier() else f"_{p}"
   ```
   For `$schemaRef`, this resulted in `_$schemaRef: str`. In Python, `$` is illegal anywhere in an identifier name, causing an immediate `SyntaxError: invalid syntax` when importing the generated module.
2. **Invalid Python Module Filenames:** Output filenames were constructed by directly swapping the `.json` extension with `.py` (e.g., `journal-v1.0.json` became `journal-v1.0.py`). Hyphens (`-`) and dots (`.`) in filenames prevent standard Python module importing (e.g. `import generated_dtos.eddn.journal-v1.0` is invalid syntax).

How must `ed-schema` sanitize schema property names and generated module filenames to guarantee syntactically valid, importable Python dataclasses while preserving original field mapping metadata?

---

## Decision Drivers

* **Syntactic Validity:** All generated Python files must be 100% valid Python syntax without `SyntaxError` on import.
* **Deterministic Identifier Transformation:** Non-alphanumeric characters (such as `$`, `-`, `.`) must be sanitized into valid Python identifiers (e.g. `$schemaRef` -> `schema_ref` or `schemaRef`, or `dollar_schemaRef`) without creating collisions.
* **Importable Module Filenames:** Output `.py` filenames must strictly be valid Python identifiers (lowercase alphanumeric with underscores, e.g. `journal_v1_0.py`).
* **Preserving Original Field Mapping:** Retain ability for consumers and deserializers to map between the sanitized Python attribute and the raw JSON property name.
* **Zero External Network Dependencies:** All sanitization logic must remain self-contained within `ed-schema` core/adapters.

---

## Considered Options

* **Option 1: Naive Underscore Prefixing (Status Quo).** Prepend `_` if not `str.isidentifier()`.
  *(Rejected: Does not eliminate illegal characters like `$` or hyphens inside the string).*
* **Option 2: Strict Regex Sanitization and Normalization.**
  * *Filenames:* Sanitize file stems using `re.sub(r"[^0-9a-zA-Z_]+", "_", stem).lower().strip("_")` + `.py`.
  * *Field Names:* Strip leading special characters (`$`) or replace non-alphanumeric characters with underscores. If stripping leading characters yields an empty string or starts with a digit, prefix with `_`. Specifically, map `$schemaRef` -> `schema_ref` or `schemaRef`.
  *(Chosen: Guarantees valid Python syntax and module imports across any arbitrary schema).*

---

## Decision Outcome

Chosen Option: **Option 2: Strict Regex Sanitization and Normalization**.

### 1. Module Filename Normalization
When deriving output filenames in `CompileDataclassesUseCase` and `DatamodelCodeGeneratorAdapter`:
```python
clean_stem = re.sub(r"[^0-9a-zA-Z_]+", "_", schema_path.stem).lower().strip("_")
output_filename = f"{clean_stem}.py"
```

### 2. Property Identifier Sanitization
When deriving dataclass attribute names:
```python
def sanitize_identifier(name: str) -> str:
    # Strip leading dollar signs or symbols common in JSON Schema
    stripped = name.lstrip("$")
    # Replace any non-alphanumeric character with underscore
    sanitized = re.sub(r"[^0-9a-zA-Z_]+", "_", stripped)
    sanitized = sanitized.strip("_")
    # Fallback if empty or starts with digit
    if not sanitized:
        sanitized = "field"
    elif sanitized[0].isdigit():
        sanitized = f"field_{sanitized}"
    # Avoid Python keywords
    if keyword.iskeyword(sanitized):
        sanitized = f"{sanitized}_"
    return sanitized
```

### 3. Consequences
* **Positive:** Generated DTO modules can be imported directly using standard Python `import` statements.
* **Positive:** Upstream schemas containing `$schemaRef` (EDDN), `$id`, or kebab-case keys compile into clean, syntactically valid dataclasses.
* **Negative:** Deserializers mapping JSON to DTO kwargs must account for the sanitized field name mapping.
