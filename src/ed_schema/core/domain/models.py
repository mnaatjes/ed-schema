"""Pure domain models, entities, and value objects for ed-schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ed_schema.core.domain.exceptions import DomainError, DomainValidationError


@dataclass(frozen=True)
class SchemaKey:
    """Universal 4-tuple composite locator for any registered API contract."""

    namespace: str
    endpoint: str
    discriminator_field: str | None = None
    discriminator_value: str | None = None

    def __post_init__(self) -> None:
        if not self.namespace or not self.namespace.strip():
            raise DomainValidationError("SchemaKey 'namespace' must be a non-empty string.")
        if not self.endpoint or not self.endpoint.strip():
            raise DomainValidationError("SchemaKey 'endpoint' must be a non-empty string.")
        if not self.endpoint.startswith("/"):
            raise DomainValidationError(
                f"SchemaKey 'endpoint' must begin with '/': {self.endpoint}"
            )
        if (self.discriminator_field is None) ^ (self.discriminator_value is None):
            raise DomainValidationError(
                "SchemaKey discriminator_field and discriminator_value must both be set "
                "or both be None."
            )


@dataclass(frozen=True)
class HeaderParameterContract:
    """Contract declaration for a single HTTP header parameter."""

    name: str
    required: bool = True
    regex_pattern: str | None = None
    default_value: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainValidationError("HeaderParameterContract 'name' cannot be empty.")
        object.__setattr__(self, "name", self.name.lower().strip())


@dataclass(frozen=True)
class HeaderContract:
    """Immutable collection of header parameter requirements."""

    parameters: tuple[HeaderParameterContract, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, tuple):
            raise DomainValidationError("HeaderContract 'parameters' must be a tuple.")

    def get(self, name: str) -> HeaderParameterContract | None:
        """Finds a header contract parameter by case-insensitive name."""
        normalized = name.lower().strip()
        for param in self.parameters:
            if param.name == normalized:
                return param
        return None


@dataclass(frozen=True)
class EndpointContract:
    """Declares an endpoint mapping within a provider manifest."""

    route: str
    schema_file: str
    discriminator_field: str | None = None
    discriminator_value: str | None = None
    header_contract: HeaderContract | None = None

    def __post_init__(self) -> None:
        if not self.route or not self.route.startswith("/"):
            raise DomainValidationError(
                f"EndpointContract 'route' must start with '/': {self.route}"
            )
        if not self.schema_file or not self.schema_file.endswith(".json"):
            raise DomainValidationError(
                f"EndpointContract 'schema_file' must be a .json file: {self.schema_file}"
            )


@dataclass(frozen=True)
class SchemaDescriptor:
    """Complete contract bundle for a single API endpoint target."""

    key: SchemaKey
    schema_definition: dict[str, Any]
    model_cls: type | None = None
    header_contract: HeaderContract | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_definition, dict):
            raise DomainValidationError("SchemaDescriptor 'schema_definition' must be a dict.")


@dataclass(frozen=True)
class SchemaValidationError(DomainError):
    """Details a specific constraint violation in a payload or header."""

    path: str
    message: str
    validator: str

    def __post_init__(self) -> None:
        if not self.message:
            raise DomainValidationError("SchemaValidationError 'message' cannot be empty.")


@dataclass(frozen=True)
class ValidationResult:
    """Immutable pre-flight validation status across headers and payload."""

    is_valid: bool
    payload_errors: tuple[SchemaValidationError, ...] = ()
    header_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.payload_errors, tuple):
            raise DomainValidationError("ValidationResult 'payload_errors' must be a tuple.")
        if not isinstance(self.header_errors, tuple):
            raise DomainValidationError("ValidationResult 'header_errors' must be a tuple.")

    @property
    def has_errors(self) -> bool:
        """Returns True if any validation or header error is present."""
        return not self.is_valid or bool(self.payload_errors or self.header_errors)


@dataclass(frozen=True)
class ParityMismatch:
    """Describes a specific structural mismatch between schema and DTO."""

    entity_name: str
    attribute_name: str
    mismatch_type: str
    description: str

    def __post_init__(self) -> None:
        if not self.entity_name:
            raise DomainValidationError("ParityMismatch 'entity_name' cannot be empty.")


@dataclass(frozen=True)
class ParityReport:
    """Summary report of schema-to-model AST synchronization."""

    namespace: str
    is_synchronized: bool
    mismatches: tuple[ParityMismatch, ...] = ()

    def __post_init__(self) -> None:
        if not self.namespace:
            raise DomainValidationError("ParityReport 'namespace' cannot be empty.")
        if not isinstance(self.mismatches, tuple):
            raise DomainValidationError("ParityReport 'mismatches' must be a tuple.")


__all__ = (
    "SchemaKey",
    "HeaderParameterContract",
    "HeaderContract",
    "EndpointContract",
    "SchemaDescriptor",
    "SchemaValidationError",
    "ValidationResult",
    "ParityMismatch",
    "ParityReport",
)
