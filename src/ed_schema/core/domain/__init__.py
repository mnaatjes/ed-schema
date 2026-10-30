"""Pure domain models, entities, and value objects."""

from ed_schema.core.domain.exceptions import (
    ContractViolationError,
    DomainError,
    DomainValidationError,
    HealthCheckFailedError,
    SchemaCompilationError,
    SchemaParityError,
    SchemaRegistrationError,
    SchemaStorageError,
)
from ed_schema.core.domain.health import HealthStatus
from ed_schema.core.domain.models import (
    EndpointContract,
    HeaderContract,
    HeaderParameterContract,
    ParityMismatch,
    ParityReport,
    SchemaDescriptor,
    SchemaKey,
    SchemaValidationError,
    ValidationResult,
)

__all__ = (
    "DomainError",
    "DomainValidationError",
    "SchemaRegistrationError",
    "ContractViolationError",
    "SchemaParityError",
    "SchemaCompilationError",
    "SchemaStorageError",
    "HealthCheckFailedError",
    "HealthStatus",
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
