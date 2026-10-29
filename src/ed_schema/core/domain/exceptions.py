"""Pure domain exceptions for ed-schema."""

from __future__ import annotations


class DomainError(Exception):
    """Base domain exception. All domain errors must inherit from this root."""


class DomainValidationError(DomainError):
    """Raised when an entity or value object fails invariant self-validation."""


class SchemaRegistrationError(DomainError):
    """Raised when registering an invalid or colliding SchemaKey."""


class ContractViolationError(DomainError):
    """Raised when pre-flight validation fails prior to network dispatch."""


class SchemaParityError(DomainError):
    """Raised when on-disk models diverge from canonical JSON schemas."""


class SchemaCompilationError(DomainError):
    """Raised when build-time code generation encounters fatal syntax errors."""


class HealthCheckFailedError(DomainError):
    """Raised when an assertive operational health check fails."""


__all__ = (
    "DomainError",
    "DomainValidationError",
    "SchemaRegistrationError",
    "ContractViolationError",
    "SchemaParityError",
    "SchemaCompilationError",
    "HealthCheckFailedError",
)
