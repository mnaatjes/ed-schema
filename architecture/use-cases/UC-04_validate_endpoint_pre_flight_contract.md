---
title: "Use-Case Specification: UC-04 Validate Endpoint Pre-Flight Contract"
use_case_id: "UC-04"
status: "approved"
version: "1.0.0"
level: "sea_level"
primary_actor: "Consumer Client / Dispatch Pipeline (ed-connectors)"
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
tags: ["use-case", "requirements", "validation", "headers", "contracts", "pre-flight"]
---

# Use-Case Specification: UC-04 Validate Endpoint Pre-Flight Contract

## 1. System Boundary and Scope

```text
+-----------------------------------------------------------------------------------+
| System Boundary: ed-schema (Composite Pre-Flight Validation Engine)               |
|                                                                                   |
|  [Actor: Connector Client / Dispatch Router]                                      |
|       |                                                                           |
|       | 1. validate_call(descriptor, headers_dict, payload_dict)                  |
|       v                                                                           |
|  +--------------------+    +---------------------+    +------------------------+  |
|  | Header Validator   | -> | Schema Validator    | -> | ValidationResult       |  |
|  | (Regex & Keys)     |    | (Draft-07/2020-12)  |    | (is_valid: bool)       |  |
|  +--------------------+    +---------------------+    +------------------------+  |
|                                                                    |              |
|                                                                    v              |
|                                                     [Pass to ed-transport]        |
|                                                     (Zero Network Sockets Wasted) |
+-----------------------------------------------------------------------------------+
```

### 1.1 In-Scope
* Composite pre-flight validation evaluating outbound HTTP header rules and payload body JSON schemas simultaneously.
* Enforcing case-insensitive header constraints (presence, default values, and regex patterns).
* Evaluating JSON schema constraints across draft-07 and draft 2020-12 specifications.
* Returning an immutable `ValidationResult` with explicit error lists (`header_errors`, `payload_errors`) executing in microseconds ($\le 50 \mu\text{s}$).

### 1.2 Out-of-Scope
* **Secret Storage & Credential Injection:** Does not store secret tokens (credentials are injected dynamically by `ed-transport`).
* **Physical Network Execution:** Does not open sockets or handle HTTP response parsing (owned by `ed-transport`).

---

## 2. Actors and Stakeholders

* **Primary Actor:** Consuming Application or Integration Client (`ed-connectors`).
* **Secondary Actor (Driven):** Downstream Transport Dispatcher (`ed-transport`).
* **Stakeholder (Operator):** Demands zero socket waste on malformed requests, immediate local failure diagnostics, and zero invalid requests reaching third-party API providers.

---

## 3. Pre-conditions and Post-conditions

### 3.1 Pre-conditions
1. The target endpoint contract is registered in `CompositeSchemaRegistry` under its `SchemaDescriptor`.
2. The calling code supplies a dictionary of assembled HTTP headers and an optional body payload.
3. The registry is loaded and accessible in memory.

### 3.2 Post-conditions
1. **Success:** Returns `ValidationResult(is_valid=True, header_errors=(), payload_errors=())`, authorizing immediate dispatch via `ed-transport`.
2. **Failure:** Returns `ValidationResult(is_valid=False, ...)` containing specific header format violations or payload schema mismatch messages without touching the network.

---

## 4. Main Success Scenario (Basic Flow)

1. The connector client prepares an outbound API call and invokes `SchemaEngine.validate_call(descriptor, headers, payload)`.
2. `SchemaEngine` delegates to `ValidateEndpointCallUseCase`.
3. The use case retrieves the registered `EndpointContract` matching the `descriptor`.
4. The driven `HeaderValidatorPort` inspects the supplied `headers`:
   - Checks that all `HeaderRequirement.REQUIRED` headers are present (case-insensitively).
   - Validates that values conform to declared regex patterns (e.g. `Authorization: Bearer <token>`).
5. If a `payload` is provided and the contract declares a `request_body_schema`, the driven `SchemaValidatorPort` validates the payload against the stored JSON Schema.
6. Zero validation errors are found in headers or payload.
7. The use case returns `ValidationResult(is_valid=True)`.
8. The caller inspects `result.is_valid`, wraps the request in an `HttpRequest`, and dispatches via `ed-transport`.

---

## 5. Alternative and Failure Flows (Extensions)

* **3a. Contract Not Registered in Registry:**
  1. No contract exists matching the provided `SchemaDescriptor`.
  2. The use case raises `SchemaNotFoundError(descriptor)`.
  3. Dispatch halts immediately.

* **4a. Missing Required Header:**
  1. A required header (e.g. `Authorization`) is absent from the `headers` dictionary.
  2. The header validator records: `"Required header 'Authorization' is missing"`.
  3. The use case returns `ValidationResult(is_valid=False, header_errors=(...))`.
  4. The client halts dispatch and logs the configuration error without sending a doomed HTTP request.

* **4b. Header Value Violates Regex Pattern:**
  1. The `Authorization` header is present but contains `"Basic 123"` instead of matching `^Bearer [a-zA-Z0-9_\-\.]+$`.
  2. The header validator records a pattern mismatch error.
  3. The use case returns `ValidationResult(is_valid=False, header_errors=(...))`.

* **5a. Payload Violates JSON Schema:**
  1. The payload dictionary is missing a required property or contains an invalid data type.
  2. The schema validator records detailed JSON Schema error paths (e.g. `'credits' must be an integer`).
  3. The use case returns `ValidationResult(is_valid=False, payload_errors=(...))`.

---

## 6. Traceability and Mitigations

* **Mitigates:** [RISK-05](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md), [RISK-09](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/risk/risk-list.md).
* **Governing Decisions:** [ADR 0005](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0005_composite_pre_flight_endpoint_and_header_contract_validation.md), [ADR 0006](file:///home/michael/src/github.com/mnaatjes/ed-schema/architecture/adr/0006_programmatic_driving_adapter_facade_definition.md).
