# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core domain model entities, composite registry, and hierarchy exceptions under `src/ed_schema/core/domain/` (`SDD-002`, `ADR 0001`, `ADR 0004`, `ADR 0005`).
- Declarative compiled model class binding on `EndpointContract` forwarding to `SchemaDescriptor.model_cls` (`ADR 0009`, `SDD-006`).
- Hexagonal boundary port definitions across driving (`SchemaRegistryPort`, `SchemaValidatorPort`, `SchemaCompilerPort`, `ParityVerifierPort`) and driven (`SchemaStoragePort`, `SchemaParserPort`, `HeaderValidatorPort`, `DatamodelGeneratorPort`) interfaces under `src/ed_schema/core/ports/` (`SDD-002`).
- Reusable in-memory test doubles (`FakeSchemaStorageAdapter`, `FakeSchemaParserAdapter`, `FakeDatamodelGeneratorAdapter`, `FakeHeaderValidatorAdapter`) under `tests/doubles/fake_schema_adapters.py`.
- Stateless core use case interactors (`RegisterSchemaUseCase`, `CompileDataclassesUseCase`, `VerifySchemaParityUseCase`, `ValidatePreFlightContractUseCase`) under `src/ed_schema/core/use_cases/` with comprehensive unit test coverage (`SDD-003`, `UC-01` through `UC-04`).
- Concrete secondary SPI driven adapters (`FileSystemSchemaStorageAdapter`, `RegexHeaderValidatorAdapter`, `JsonSchemaParserAdapter`, `DatamodelCodeGeneratorAdapter`) under `src/ed_schema/adapters/driven/` (`SDD-004`).
- Unified programmatic driving adapter facade (`SchemaEngine`) and composition root (`Container`, `create_schema_engine`) with package-root re-exports (`SDD-005`, `ADR 0006`).
- Software Design Documents [`SDD-002`](architecture/designs/0002_core_domain_and_ports_architecture.md), [`SDD-003`](architecture/designs/0003_core_use_cases_and_interactors_architecture.md), [`SDD-004`](architecture/designs/0004_driven_adapters_architecture.md), [`SDD-005`](architecture/designs/0005_composition_root_and_driving_facade_architecture.md), and [`SDD-006`](architecture/designs/0006_endpoint_contract_model_class_binding_architecture.md).

## [0.1.0] - 2026-10-29

### Added
- Initial project architecture scaffolding adhering to pure Hexagonal Architecture (Ports and Adapters).
- Multi-namespace composite schema registry and manifest ingestion core (`ADR 0001`).
- Programmatic build-time Python dataclass compilation and AST parity verification design (`ADR 0002`, `ADR 0003`).
- DTO naming conventions with provider prefix scoping and lexical isolation (`ADR 0004`).
- Composite pre-flight endpoint and HTTP header contract validation (`ADR 0005`).
- Unified programmatic driving adapter facade (`SchemaEngine`) specification (`ADR 0006`).
- Consumer build pipeline and parity test harness patterns (`ADR 0007`).
- Multi-tier architectural scope and boundary enforcement mechanisms (`ADR 0008`, `SDD-001`).
- Comprehensive Unified Process specifications: Use Cases (`UC-01` through `UC-04`), Master Risk Register (`risk-list.md`), and RFC 0001 fleet unification alignment.
- Automated versioning configuration using `bump-my-version`.
