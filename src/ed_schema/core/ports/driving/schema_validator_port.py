"""Driving port contract for pre-flight payload and header validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ed_schema.core.domain.models import SchemaKey, ValidationResult
from ed_schema.core.ports.base import DrivingPort


@runtime_checkable
class SchemaValidatorPort(DrivingPort, Protocol):
    """Primary port for executing composite pre-flight validation gates."""

    def validate_payload(self, key: SchemaKey, payload: dict[str, Any]) -> ValidationResult:
        """Validates a dictionary payload against the schema registered under key."""
        ...

    def validate_headers(self, key: SchemaKey, headers: Mapping[str, str]) -> ValidationResult:
        """Validates HTTP request headers against the contract registered under key."""
        ...

    def validate_call(
        self,
        key: SchemaKey,
        headers: Mapping[str, str],
        payload: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Unified pre-flight validation gate verifying both headers and payload."""
        ...


__all__ = ["SchemaValidatorPort"]
