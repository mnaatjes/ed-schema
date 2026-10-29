# Master Implementation Checklist: Scope and Boundary Enforcement

This checklist provides an exhaustive, phase-by-phase implementation tracking system systematically derived from [ADR 0008](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0008_scope_and_boundary_enforcement_mechanisms.md) and [SDD-001](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/designs/0001_scope_and_boundary_enforcement_architecture.md).

---

## 1. Tier 1: Local Pre-Commit Authoring Gate (`.pre-commit-config.yaml`)
*Governing References: ADR 0008 § Tier 1; SDD-001 § 3.1*

- [x] **1.1 Fast Hygiene Hooks Execution Verification:**
  - [x] `trailing-whitespace`: Assert stripping of trailing whitespace across all source and markdown files.
  - [x] `end-of-file-fixer`: Assert POSIX trailing newline enforcement across all repository files.
  - [x] `check-yaml`: Assert validation of all YAML manifests, workflows, and configs.
  - [x] `check-toml`: Assert syntax integrity of `pyproject.toml`.
  - [x] `ruff`: Enforce PEP 8 rules, naming conventions, and import sorting.
  - [x] `ruff-format`: Enforce deterministic code formatting.
  - [x] Verify sub-second ($<1.5\text{s}$) total execution overhead for the hook suite.

---

## 2. Tier 2: In-Process Verification Engine & Boundary Contracts
*Governing References: ADR 0008 § Tier 2; SDD-001 § 3.2; RISK-01 to RISK-07, RISK-10*

### 2.1 Import Linter Architecture (`.importlinter`)
- [x] **2.1.1 External Fleet & Network Isolation Contract:**
  - Add `external_fleet_and_network_isolation` forbidden contract across `ed_schema`:
    - Forbidden game domain packages: `ed_models` (*RISK-04*).
    - Forbidden network/socket engines: `ed_transport`, `requests`, `httpx`, `aiohttp`, `urllib` (*RISK-05*).
    - Forbidden subprocess/shell execution: `subprocess` (*UC-02 non-goal*).
- [x] **2.1.2 Verify Hexagonal Internal Layer Contracts:**
  - [x] `core_domain_isolation`: Verify `core.domain` has zero imports of ports, use cases, or adapters.
  - [x] `inward_dependency_direction`: Verify inward dependency flow (`adapters` $\rightarrow$ `use_cases` $\rightarrow$ `domain`).
  - [x] `domain_port_isolation`: Verify `domain` does not import ports or external libs.
  - [x] `use_case_transport_isolation`: Verify `use_cases` remain transport- and framework-agnostic.
  - [x] `composition_root_isolation`: Verify adapter wiring is confined exclusively to `bootstrap/`.

### 2.2 AST Compliance & Architectural Tests (`tests/architecture/test_boundaries.py`)
- [x] **2.2.1 Dynamic Code Execution Banning (`test_zero_dynamic_code_execution`):**
  - Implement `BannedCallVisitor` scanning AST `Call` nodes across `src/ed_schema/`.
  - Prohibit `eval()`, `exec()`, and `compile()` (*RISK-03*, *ADR 0002*).
- [x] **2.2.2 Network I/O and Socket Import Banning (`test_zero_network_io_in_library`):**
  - Scan AST `Import` and `ImportFrom` nodes across `src/ed_schema/`.
  - Prohibit modules: `socket`, `http`, `urllib`, `requests`, `httpx`, `aiohttp`, `websocket` (*RISK-05*, *ADR 0005*).
- [x] **2.2.3 Game Domain Vocabulary Banning (`test_zero_game_domain_leakage`):**
  - Scan identifiers, class names, function names, and variable names in `src/ed_schema/core/domain/`.
  - Prohibit domain tokens: `Commander`, `Ship`, `StarSystem`, `Journal`, `Commodity`, `Station`, `Market` (*RISK-04*, *ADR 0004*).
- [x] **2.2.4 Domain Entity Immutability & Self-Validation (`test_domain_entities_are_self_validating`):**
  - Inspect all entity classes in `src/ed_schema/core/domain/` (`SchemaKey`, `SchemaDescriptor`, `EndpointContract`, `HeaderParameterContract`).
  - Assert `@dataclass(frozen=True)` decoration and presence of `__post_init__` validation guards.
- [ ] **2.2.5 DTO Lexical Scope Isolation & Explicit Exports (`test_dto_lexical_scope_isolation`):**
  - Verify compiled dataclass modules generate explicit `__all__` tuples containing only public DTO classes.
  - Assert zero leakage of generator internals or external helper names (*RISK-06*, *ADR 0004*).
- [ ] **2.2.6 Multi-Namespace Identifier Collision Safety (`test_multi_namespace_collision_safety`):**
  - Assert 4-tuple key uniqueness `(namespace, endpoint, discriminator_field, discriminator_value)`.
  - Verify disparate providers with identical resource names (e.g. `capi/profile.json` vs `inara/profile.json`) generate distinct prefixed classes (`CapiProfileResponseDTO` vs `InaraProfileEventDataDTO`) (*RISK-02*, *ADR 0001*, *ADR 0004*).
- [x] **2.2.7 Banned Long-Running Daemons and Service Loops (`test_zero_daemon_service_loops`):**
  - Assert zero infinite loops (`while True:`) or background daemon threading primitives inside `src/ed_schema/` (*ADR 0008 out-of-scope*).
- [ ] **2.2.8 Schema Compilation Caching & Performance Degradation Guard (`test_schema_validation_caching`):**
  - Verify validator adapter caches compiled schema validators in memory to prevent repeated parse overhead (*RISK-10*).

### 2.3 Verification Orchestration (`scripts/verify.py`)
- [x] **2.3.1 Step Execution Integration:** Ensure pre-commit, import linter, mypy, and all pytest architecture tests run sequentially and exit on first failure.
- [x] **2.3.2 Latency Ceiling:** Ensure the complete `scripts/verify.py` run finishes in $<15\text{s}$ locally.

---

## 3. Tier 3: Cross-Platform Wine Simulation (`scripts/run_wine_tests.sh`)
*Governing References: ADR 0008 § Tier 3; SDD-001 § 3.3; RISK-08*

- [x] **3.1 Simulation Environment Setup:**
  - Audit `scripts/run_wine_tests.sh` to configure isolated `WINEPREFIX` and silent `WINEDEBUG="-all"`.
  - Verify Wine Python interpreter can execute package checks.
- [x] **3.2 Windows NT Path Invariant Verification:**
  - Assert package import and execution succeeds under Windows NT Python runtime via Wine simulation.
  - Verify path separator and Windows NT environment reporting.

---

## 4. Tier 4: Continuous Integration Matrix Pipeline (`.github/workflows/ci.yml`)
*Governing References: ADR 0008 § Tier 4; SDD-001 § 3.4; RISK-08, RISK-09*

- [x] **4.1 Multi-Platform Matrix Expansion:**
  - Configure matrix jobs for `ubuntu-latest` and `windows-latest`.
  - Configure Python versions: `3.11`, `3.12`, `3.13`.
- [x] **4.2 Deterministic Build-Time Parity Verification Step:**
  - Add `git diff --exit-code` drift check step in CI workflow.

---

## 5. Verification & Acceptance Sign-Off

- [x] All Tier 1 pre-commit hooks pass locally.
- [x] `.venv/bin/lint-imports` evaluates all 6 contracts with 0 violations.
- [x] `.venv/bin/mypy --strict` passes with 0 issues.
- [x] All architectural AST compliance tests pass in `tests/architecture/test_boundaries.py` (32/32 passed).
- [x] `scripts/run_wine_tests.sh` passes successfully in Wine environment.
- [x] Full quality gate `scripts/verify.py` passes with exit code 0.
