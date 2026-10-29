# Context & Developer Environment Guide: `ed-schema`

## 1. Project Overview & Architecture
`ed-schema` is a pure Hexagonal Architecture (Ports and Adapters) contract, schema governance, and code-generation engine for the *Elite Dangerous* software fleet, supporting Linux (Steam / Proton / Steam Deck) and native Windows NT.

It acts as the shared architectural foundation for contract management across `ed-capi`, `ed-eddn`, `ed-inara`, and `ed-connectors`, handling:
* **Standard JSON Schema Baseline:** Ingestion, storage, and validation of Draft-07 and Draft 2020-12 JSON Schemas.
* **Universal API Composition Registry:** Indexing 1:1 direct REST endpoints, 1:N root-level polymorphic discriminators (EDDN `$schemaRef`), and 1:N nested batch-item RPC discriminators (Inara `events[*].eventName`) through a single unified composite key `(namespace, endpoint, discriminator_field, discriminator_value)`.
* **Abstract HTTP Header Contract Modeling:** Declaring, validating, and generating typed DTOs for case-insensitive HTTP headers across static protocol, injected auth, and dynamic operational categories.
* **Deterministic Build-Time Code Generation:** Programmatic and CLI compilation of canonical JSON schemas into high-performance Python dataclasses using `datamodel-code-generator` without dynamic runtime code evaluation.
* **Automated Drift & Parity Verification:** CLI and CI tooling (`ed-schema verify-parity`) to guarantee synchronized state between stored schemas and generated Python source models.
* **Strict Business-Logic Ignorance:** Zero domain entities or knowledge of Elite Dangerous ships, stars, commanders, or journals.

### Architectural Layout (`src/ed_schema/`)
- `src/ed_schema/core/domain/`: Pure domain core entities (`SchemaKey`, `SchemaDescriptor`, `EndpointContract`, `HeaderParameterContract`, `CompositeSchemaRegistry`). Zero imports of external validation engines, operating system APIs, or game models.
- `src/ed_schema/core/ports/`: Domain boundary contracts:
  - `driving/`: Primary ports exposed to consumer applications (`SchemaRegistryPort`, `SchemaValidatorPort`, `SchemaGeneratorPort`).
  - `driven/`: Secondary SPIs implemented by adapters (`SchemaStoragePort`, `SchemaParserPort`, `CodeGeneratorPort`, `HeaderValidatorPort`).
- `src/ed_schema/core/use_cases/`: Stateless use case interactors (`ValidatePayloadUseCase`, `RegisterSchemaUseCase`, `GenerateDataclassesUseCase`, `VerifyParityUseCase`).
- `src/ed_schema/adapters/`:
  - `driving/`: Programmatic client facades (`SchemaEngine`) and developer CLI tool suites (`ed_schema.adapters.driving.cli`).
  - `driven/`: Concrete implementations (`validator/` for `jsonschema`/`fastjsonschema`, `codegen/` for `datamodel-code-generator`, `inference/` for `genson`, `storage/` for filesystem schema repositories).
- `src/ed_schema/bootstrap/`: Composition root (`Container`, `create_schema_engine`) wiring ports, interactors, and adapters.

---

## 2. Python Virtual Environment & Tooling Paths

The project uses a local virtual environment located at `.venv/` in the repository root:

* **Python Interpreter:** `.venv/bin/python`
* **Pytest:** `.venv/bin/pytest`
* **Ruff (Linter & Formatter):** `.venv/bin/ruff`
* **Import Linter:** `.venv/bin/lint-imports`
* **Type Checker:** `.venv/bin/mypy`

> [!IMPORTANT]
> Always execute commands and tests directly using `.venv/bin/<tool>` (e.g. `.venv/bin/python scripts/verify.py` or `.venv/bin/pytest`).

---

## 3. Standard Verification Commands

All changes must pass Tier 2 Quality Gates:

```bash
# 1. Complete Tier 2 Quality Gates (Pre-commit, Ruff lint/format, Import linter, MyPy, Pytest suite):
.venv/bin/python scripts/verify.py

# 2. Targeted Unit and Architectural Boundary Tests:
.venv/bin/pytest tests/architecture/test_boundaries.py

# 3. Import Boundary Linter (verifies Hexagonal isolation invariants):
.venv/bin/lint-imports

# 4. Local Wine Windows NT Simulation (cross-platform verification):
./scripts/run_wine_tests.sh
```

---

## 4. Context Hydration & Traceability

* **Parent Architectural Specification:** [ed-telemetry ADR 0035: Integration Fleet Decomposition and Boundary Taxonomy](file:///home/michael/src/github.com/mnaatjes/ed-telemetry/architecture/adr/0035_integration_fleet_decomposition_and_boundary_taxonomy.md)
* **Sibling Transport Foundation:** [ed-transport](https://github.com/mnaatjes/ed-transport.git)
* **Governing Template:** [python-hexagonal-template](https://github.com/mnaatjes/python-hexagonal-template.git)
* **Unified Process Documentation:**
  * Master Architectural Governance Root: [`architecture/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/README.md)
  * Master Risk Register: [`architecture/risk/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/README.md)
  * Use-Case Specifications: [`architecture/use-cases/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/use-cases/README.md)
  * Architectural Decision Records:
    * [`ADR 0001: Multi-Namespace Manifest Loading and Composite Schema Registry`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0001_multi_namespace_manifest_loading_and_composite_schema_registry.md)
    * [`ADR 0002: Programmatic Build-Time Dataclass Compilation`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0002_programmatic_build_time_dataclass_compilation.md)
    * [`ADR 0003: Granular In-Process Parity Verification`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0003_granular_in_process_parity_verification.md)
    * [`ADR 0004: DTO Naming Conventions and Lexical Scope Isolation`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0004_dto_naming_conventions_and_lexical_scope_isolation.md)
    * [`ADR 0005: Composite Pre-Flight Endpoint and Header Contract Validation`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0005_composite_pre_flight_endpoint_and_header_contract_validation.md)
  * Software Design Documents: [`architecture/designs/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/README.md)
  * Engineering Proposals: [`architecture/rfcs/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/rfcs/README.md)
  * Boundary Contracts: [`architecture/api/README.md`](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/api/README.md)
* **Conversation ID:** `0ed81619-2390-4109-94c2-75e8bcbec353`
