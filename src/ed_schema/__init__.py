"""Package root for ed_schema."""

from __future__ import annotations

from ed_schema.adapters.driving.schema_engine import SchemaEngine
from ed_schema.bootstrap.client_factory import create_schema_engine
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

__version__ = "0.1.0"

__all__ = (
    "ContractViolationError",
    "DomainError",
    "DomainValidationError",
    "EndpointContract",
    "HeaderContract",
    "HeaderParameterContract",
    "HealthCheckFailedError",
    "ParityMismatch",
    "ParityReport",
    "SchemaCompilationError",
    "SchemaDescriptor",
    "SchemaEngine",
    "SchemaKey",
    "SchemaParityError",
    "SchemaRegistrationError",
    "SchemaStorageError",
    "SchemaValidationError",
    "ValidationResult",
    "__version__",
    "create_schema_engine",
)
