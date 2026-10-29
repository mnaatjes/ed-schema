---
title: "ADR 0007: Consumer Build Pipeline and Parity Test Harness Patterns"
status: "accepted"
date: "2026-10-29"
deciders: ["Core Architecture Team"]
consulted: ["ADR 0002 (ed-schema)", "ADR 0003 (ed-schema)", "ADR 0006 (ed-schema)", "RFC 0001 (ed-schema)"]
informed: ["All Engineers", "Integration Client Authors (ed-connectors)"]
tags: ["adr", "architecture", "build-pipeline", "scripts", "parity-tests", "pre-commit"]
---

# ADR 0007: Consumer Build Pipeline and Parity Test Harness Patterns

## Context and Problem Statement

`ed-schema` provides programmatic build-time model generation ([ADR 0002](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0002_programmatic_build_time_dataclass_compilation.md)), in-process AST parity verification ([ADR 0003](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0003_granular_in_process_parity_verification.md)), and a unified driving facade `SchemaEngine` ([ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md)).

However, a library cannot enforce quality if consuming repositories (`ed-connectors`) implement build scripts and test harnesses in an ad-hoc, inconsistent manner:
- Some developers might write custom shell loops calling private APIs.
- Parity tests might be omitted from local pre-commit gates, allowing schema drift to escape until remote CI runs.
- Missing standardized script paths (`scripts/compile_models.py`) creates onboarding confusion across the fleet.

How should consuming packages (`ed-connectors`) standardize their internal build scripts, test fixtures, and pre-commit hooks to integrate with `ed-schema` seamlessly?

---

## Decision Drivers

* **Fleet Standardization:** All consumer repositories adopt identical script conventions (`scripts/compile_models.py`) and test layouts (`tests/architecture/test_schema_parity.py`).
* **Turn-Key Pre-Commit Integration:** Pre-commit hooks must catch schema drift locally in under 1 second before git commits are created.
* **Hermetic & Cross-Platform:** Scripts must execute identically under Linux virtual environments (`.venv/bin/python`) and native Windows NT PowerShell.
* **Fail-Fast Pytest Integration:** Parity checks must run as standard unit/architecture tests within `pytest` and report clear, actionable AST diffs.

---

## Decision Outcome

Chosen Option: **Standardized Consumer Build Pipeline, Test Harness, and Pre-Commit Blueprint**.

### 1. Consumer Script Pattern (`scripts/compile_models.py`)

Every consumer package maintaining provider schemas establishes an idempotent compilation script located at `scripts/compile_models.py`:

```python
#!/usr/bin/env python3
"""Canonical build-time model compiler for consumer packages.

Usage:
    .venv/bin/python scripts/compile_models.py
"""

from pathlib import Path
import sys
from ed_schema import SchemaEngine

# Root directory of the consuming repository:
REPO_ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_ROOT = REPO_ROOT / "src" / "ed_connectors" / "providers"


def compile_all_providers() -> int:
    """Discovers provider subpackages and compiles schemas into typed DTOs."""
    engine = SchemaEngine()
    total_compiled = 0

    if not PROVIDERS_ROOT.exists():
        print(f"Error: Providers root not found at {PROVIDERS_ROOT}")
        return 1

    # Discovers subpackages with a schemas/ directory:
    for provider_dir in sorted(PROVIDERS_ROOT.iterdir()):
        schema_dir = provider_dir / "schemas"
        models_dir = provider_dir / "models"

        if provider_dir.is_dir() and schema_dir.exists():
            models_dir.mkdir(parents=True, exist_ok=True)
            provider_name = provider_dir.name
            class_prefix = provider_name.capitalize()

            print(
                f"[COMPILE] Provider '{provider_name}' -> models/ (Prefix: {class_prefix})"
            )
            compiled_files = engine.compile_models(
                schema_dir=schema_dir,
                output_dir=models_dir,
                class_prefix=class_prefix,
            )
            total_compiled += len(compiled_files)

    print(
        f"[SUCCESS] Compiled {total_compiled} Python model files across providers."
    )
    return 0


if __name__ == "__main__":
    sys.exit(compile_all_providers())
```

---

### 2. Architecture Test Harness Pattern (`test_schema_parity.py`)

Every consumer package includes an architectural parity test suite under `tests/architecture/test_schema_parity.py`:

```python
"""Architectural test suite guaranteeing zero schema drift."""

from pathlib import Path
import pytest
from ed_schema import SchemaEngine, SchemaParityError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDERS_ROOT = REPO_ROOT / "src" / "ed_connectors" / "providers"

# Parametrize test across all active provider subpackages:
PROVIDER_NAMES = [
    p.name
    for p in PROVIDERS_ROOT.iterdir()
    if p.is_dir() and (p / "schemas").exists()
]


@pytest.mark.architecture
@pytest.mark.parametrize("provider", PROVIDER_NAMES)
def test_provider_models_in_parity_with_schemas(provider: str) -> None:
    """Guarantees on-disk models match canonical JSON schemas AST-for-AST."""
    engine = SchemaEngine()
    provider_dir = PROVIDERS_ROOT / provider
    schema_dir = provider_dir / "schemas"
    models_dir = provider_dir / "models"

    try:
        report = engine.verify_parity(
            schema_dir=schema_dir,
            models_dir=models_dir,
            namespace=provider,
            class_prefix=provider.capitalize(),
        )
        assert (
            report.is_synchronized
        ), f"Provider '{provider}' models are out of sync with schemas!"
    except SchemaParityError as err:
        pytest.fail(
            f"Schema parity failure in provider '{provider}':\n{err.diff_summary}"
        )
```

---

### 3. Pre-Commit Hook Configuration (`.pre-commit-config.yaml`)

To prevent uncompiled schema modifications from ever being committed to git, consumer repositories wire parity verification directly into `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: schema-parity-check
        name: verify-schema-parity
        entry: .venv/bin/pytest tests/architecture/test_schema_parity.py
        language: system
        pass_filenames: false
        files: ^(src/ed_connectors/providers/.*/schemas/.*\.json|src/ed_connectors/providers/.*/models/.*\.py)$
```

---

## Consequences

### Positive Consequences
* **Fleet Uniformity:** Every engineer across the fleet knows that running `.venv/bin/python scripts/compile_models.py` updates all models.
* **Deterministic Local Enforcement:** Developers cannot commit out-of-sync schemas; pre-commit hooks fail instantly before the commit is created.
* **Clear Diagnostic Guidance:** Failures in `test_schema_parity.py` point directly to the exact file and AST node that drifted.
* **Cross-Platform Compatibility:** Relies purely on standard Python virtual environment tools without platform-specific shell scripts.

### Negative Consequences & Mitigations
* **Requires Initial Setup in Consumer Repos:** Consumer repos must create `scripts/compile_models.py`.
  * *Mitigation:* The script blueprint will be baked into `python-hexagonal-template` and the initial `ed-connectors` scaffold.
