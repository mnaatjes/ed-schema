"""Driven port contract for JSON Schema syntax parsing and validation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ed_schema.core.domain.models import SchemaValidationError
from ed_schema.core.ports.base import DrivenPort


@runtime_checkable
class SchemaParserPort(DrivenPort, Protocol):
    """Secondary SPI for schema syntax checking and payload validation."""

    def validate_payload(
        self,
        schema_definition: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[SchemaValidationError, ...]:
        """Validates payload against schema_definition, returning any violations."""
        ...


__all__ = ["SchemaParserPort"]
