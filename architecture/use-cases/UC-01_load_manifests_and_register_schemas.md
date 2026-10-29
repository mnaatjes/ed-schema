---
title: "Use-Case Specification: UC-01 Load Manifests and Register Schemas"
use_case_id: "UC-01"
status: "approved"
version: "1.0.0"
level: "sea_level"
primary_actor: "Consumer Application / Connector Engine (ed-connectors, ed-telemetry)"
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
tags: ["use-case", "requirements", "registry", "manifest", "namespaces", "composite-key"]
---

# Use-Case Specification: UC-01 Load Manifests and Register Schemas

## 1. System Boundary and Scope

```text
+-----------------------------------------------------------------------------------+
| System Boundary: ed-schema (Registry Core & Manifest Ingestion Engine)             |
|                                                                                   |
|  [Actor: Connector Host Engine / Consumer App]                                    |
|       |                                                                           |
|       | 1. load_manifests(Sequence[ProviderManifest])                             |
|       v                                                                           |
|  +--------------------+    +---------------------+    +------------------------+  |
|  | Manifest Validator | -> | Namespace Isolator  | -> | CompositeSchemaRegistry|  |
|  +--------------------+    +---------------------+    +------------------------+  |
|                                                                    |              |
|                                                                    v              |
|                                                        [Indexed In-Memory Schema] |
|                                                        (4-Tuple Composite Key)    |
+-----------------------------------------------------------------------------------+
```

### 1.1 In-Scope
* Ingestion of standard Draft-07 and Draft 2020-12 JSON Schema files from declared filesystem directories.
* Indexing contracts across multiple provider namespaces (`capi`, `eddn`, `inara`, `spansh`) through the universal 4-tuple key: `(namespace, endpoint, discriminator_field, discriminator_value)`.
* Registration and updating of composite `EndpointContract` instances (headers + payload schema references).
* Support for all four composition patterns: 1:1 Direct REST, 1:N Root Discriminators, 1:N Batch RPC Items, and 1:1 Parameterized REST.
* Thread-safe, microsecond-latency in-memory retrieval by key or by payload inspection (`resolve_from_payload`).

### 1.2 Out-of-Scope
* **Physical Wire Dispatch:** Making HTTP network requests (owned by `ed-transport`).
* **Game Model Translation:** Transforming game events into domain models (owned by `ed-models` and `ed-telemetry`).
* **Credential Resolution:** Injecting actual secret tokens or keys into requests (owned by `ed-transport`).

---

## 2. Actors and Stakeholders

* **Primary Actor:** Consuming Application or Integration Client (`ed-connectors`, `ed-telemetry`).
* **Stakeholder (Developer / Operator):** Requires collision-free contract indexing across multiple API providers, sub-millisecond lookup latency, and strict namespace isolation.

---

## 3. Pre-conditions and Post-conditions

### 3.1 Pre-conditions
1. Stored schema files comply with standard JSON Schema Draft-07 or Draft 2020-12 syntax.
2. The calling application has instantiated or accessed `SchemaEngine`.
3. Declared manifest directories exist and are readable on the local filesystem.

### 3.2 Post-conditions
1. **Success:** All schemas and endpoint contracts are indexed within their designated namespaces in `CompositeSchemaRegistry` with zero key collisions.
2. **Failure:** If a schema contains invalid JSON or violates schema syntax, the registry rejects the manifest with a descriptive `SchemaDefinitionError` without corrupting existing registered namespaces.

---

## 4. Main Success Scenario (Basic Flow)

1. The consumer invokes `SchemaEngine.load_manifests(manifests)` during application startup.
2. For each manifest, `SchemaEngine` extracts the unique namespace (e.g. `"capi"`) and the local schema directory path.
3. The filesystem storage adapter reads all `.json` files within the directory.
4. For each schema file, `SchemaEngine` parses and validates the Draft-07/2020-12 structure.
5. `SchemaEngine` inspects the manifest's `endpoints` declarations and maps each endpoint to its 4-tuple `SchemaKey`.
6. The contract is stored in `CompositeSchemaRegistry` under its composite key.
7. `SchemaEngine` returns control to the caller with all provider contracts active and ready for in-memory resolution.

---

## 5. Alternative and Failure Flows (Extensions)

* **3a. Schema File Missing or Unreadable:**
  1. The filesystem adapter encounters an unreadable file or permission error.
  2. `SchemaEngine` raises `SchemaStorageError(path, details)`.
  3. No partial state is stored for that specific provider; prior namespaces remain untouched.

* **4a. Malformed JSON Schema Structure:**
  1. A `.json` file contains invalid JSON syntax or unparseable Draft-07 keywords.
  2. `SchemaEngine` raises `SchemaSyntaxError(file_path, parse_errors)`.
  3. Manifest registration aborts, notifying the caller of the offending schema line.

* **5a. Discriminator Field Not Found in Schema:**
  1. An endpoint specifies a 1:N discriminator field (e.g. `"$schemaRef"`), but the underlying schema lacks this property definition.
  2. `SchemaEngine` raises `DiscriminatorContractMismatchError(endpoint, field)`.

---

## 6. Traceability and Mitigations

* **Mitigates:** [RISK-03](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-06](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-08](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md).
* **Governing Decisions:** [ADR 0001](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0001_multi_namespace_manifest_loading_and_composite_schema_registry.md), [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md), [RFC 0001](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/rfcs/0001_fleet_unification_and_provider_subpackage_architecture.md).
