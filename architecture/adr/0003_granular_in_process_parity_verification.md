---
title: "ADR 0003: Granular In-Process Parity Verification"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["RFC 0001 (ed-schema)", "ADR 0001 (ed-schema)", "ADR 0002 (ed-schema)"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "parity", "verification", "ast", "testing", "ci"]
---

# ADR 0003: Granular In-Process Parity Verification

## Context and Problem Statement

When source code models (Python dataclasses) are generated from schema files (`.json`), repositories face the persistent hazard of **Contract Drift (Anti-Pattern D)**:
- A developer updates a `.json` schema in git but forgets to regenerate the corresponding `.py` model file.
- A developer manually modifies a generated `.py` file without updating the source schema.
- In both cases, the serialization models diverge silently from the wire contract, resulting in production runtime failures that bypass type checking.

In a unified `ed-connectors` architecture with multiple provider subpackages (`capi`, `eddn`, `inara`, `spansh`), running a slow, monolithic drift check across every provider on every small commit creates unnecessary developer friction.

How should `ed-schema` provide automated, rapid, and granular parity verification to guarantee synchronization between stored schemas and Python models without relying on external CLI tools?

---

## Decision Drivers

* **Zero Schema Drift Invariant:** CI and pre-commit gates must fail immediately if generated Python dataclasses do not perfectly match stored JSON schemas.
* **In-Process Python Execution:** Verification must run natively inside test frameworks (`pytest tests/architecture/test_parity.py`) without invoking subprocesses.
* **Granular Target Filtering:** Support verifying a specific provider namespace or path (e.g. only checking `inara` when editing Inara schemas) for sub-second feedback.
* **AST-Equivalence Comparison:** Compare structural AST representations rather than raw strings to ignore trivial formatting differences (e.g. trailing commas, docstring line wraps).

---

## Considered Options

* **Option 1: Manual Developer Discipline & Code Review.** Rely on reviewers to spot desynchronization during pull requests.
  *(Rejected: High failure rate; silent schema drift will inevitably escape to production).*
* **Option 2: Standalone Shell Tooling in CI Workflows.** Run an external shell script that calls a CLI command only during GitHub Actions CI.
  *(Rejected: Slow feedback loop; developers only discover drift after pushing commits).*
* **Option 3: Programmatic In-Process Parity Interactor (`VerifyParityUseCase`).** Expose `SchemaEngine.verify_parity()` callable directly within `pytest` and repository verification scripts (`scripts/verify.py`).

---

## Decision Outcome

Chosen Option: **Option 3: Programmatic In-Process Parity Interactor (`VerifyParityUseCase`)**.

### 1. Parity Verification Mechanics

```
┌────────────────────────────────────────────────────────────────────────┐
│                        In-Process Parity Engine                        │
│                                                                        │
│   1. Read on-disk schema (.json)                                       │
│   2. Compile in-memory ephemeral AST buffer                            │
│   3. Read on-disk Python model (.py) and parse AST                     │
│   4. Compare AST nodes (ast.dump / structural equivalence)             │
│   5. IF AST mismatch:                                                  │
│         Raise SchemaParityError(diff_summary)                          │
│      ELSE:                                                             │
│         Pass (Parity Verified)                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Programmatic Facade Interface

```python
class SchemaEngine:
    def verify_parity(
        self,
        schema_dir: str | Path,
        models_dir: str | Path,
        namespace: str | None = None,
        class_prefix: str = "",
    ) -> ParityReport:
        """Compares on-disk models against compiled schema ASTs in-process.

        Raises SchemaParityError if drift is detected.
        """
        use_case: VerifyParityUseCase = self._container.resolve(
            VerifyParityUseCase
        )
        return use_case.execute(
            schema_dir=Path(schema_dir),
            models_dir=Path(models_dir),
            namespace=namespace,
            class_prefix=class_prefix,
        )
```

### 3. Integration into Downstream Test Suites (`ed-connectors`)

```python
# tests/architecture/test_schema_parity.py in ed-connectors:
import pytest
from ed_schema import SchemaEngine, SchemaParityError

engine = SchemaEngine()


@pytest.mark.parametrize("provider", ["capi", "eddn", "inara", "spansh"])
def test_provider_models_in_parity_with_schemas(provider: str) -> None:
    """Guarantees Python models on disk match canonical JSON schemas exactly."""
    try:
        report = engine.verify_parity(
            schema_dir=f"src/ed_connectors/adapters/driven/providers/{provider}/schemas",
            models_dir=f"src/ed_connectors/adapters/driven/providers/{provider}/models",
            namespace=provider,
            class_prefix=provider.capitalize(),
        )
        assert report.is_synchronized
    except SchemaParityError as err:
        pytest.fail(f"Schema drift detected in provider '{provider}': {err}")
```

---

## Consequences

### Positive Consequences
* **Automated Drift Elimination:** Inability to commit or merge desynchronized models; pre-commit and CI fail deterministically.
* **Rapid Developer Feedback:** Sub-second execution when scoped to a single provider namespace via `pytest tests/test_parity.py -k inara`.
* **Clean Formatting Independence:** AST comparison ensures cosmetic formatting changes (e.g. Ruff reformats) do not trigger false positive drift warnings.
* **Pure In-Process Execution:** Fully compliant with library standards (zero subprocess shell execution).

### Negative Consequences & Mitigations
* **AST Compilation Overhead in Test Suites:** Recompiling schemas in memory during unit tests adds a small latency overhead (~100ms per provider).
  * *Mitigation:* Caching compiled ASTs across test sessions and isolating parity tests under an architecture test marker (`@pytest.mark.architecture`).
