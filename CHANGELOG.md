# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
