# ed-schema `v0.1.0`

Deterministic JSON Schema registry, contract validator, and code generation engine for Elite Dangerous

## Architectural Governance
This service is architected in accordance with Hexagonal Architecture (Ports and Adapters).
* Core Domain logic resides in `src/ed_schema/core/` with ZERO external infrastructure dependencies.
* Architectural boundaries are enforced deterministically via `import-linter` and `pytest-archon`.

## Quickstart

Run quality verification gates:
```bash
uv run python scripts/verify.py
```
