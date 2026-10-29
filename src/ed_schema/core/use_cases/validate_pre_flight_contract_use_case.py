"""Use case for composite pre-flight endpoint and header contract validation (UC-04)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ed_schema.core.domain.models import (
    SchemaDescriptor,
    SchemaKey,
    SchemaValidationError,
    ValidationResult,
)
from ed_schema.core.ports.driven.header_validator_port import HeaderValidatorPort
from ed_schema.core.ports.driven.schema_parser_port import SchemaParserPort


class ValidatePreFlightContractUseCase:
    """Orchestrates composite pre-flight validation for outgoing/incoming calls."""

    def __init__(
        self,
        registry_resolver: Callable[[SchemaKey], SchemaDescriptor | None],
        header_validator: HeaderValidatorPort,
        schema_parser: SchemaParserPort,
    ) -> None:
        self._registry_resolver = registry_resolver
        self._header_validator = header_validator
        self._schema_parser = schema_parser

    def execute(
        self,
        key: SchemaKey,
        headers: Mapping[str, str],
        payload: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validates headers and payload body against the registered contract."""
        descriptor = self._registry_resolver(key)
        if descriptor is None:
            return ValidationResult(
                is_valid=False,
                header_errors=(f"Unregistered SchemaKey: {key}",),
            )

        header_errors: tuple[str, ...] = ()
        if descriptor.header_contract is not None:
            header_errors = self._header_validator.validate_headers(
                contract=descriptor.header_contract,
                headers=headers,
            )

        payload_errors: tuple[SchemaValidationError, ...] = ()
        if payload is not None:
            payload_errors = self._schema_parser.validate_payload(
                schema_definition=descriptor.schema_definition,
                payload=payload,
            )

        is_valid = len(header_errors) == 0 and len(payload_errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            payload_errors=payload_errors,
            header_errors=header_errors,
        )


__all__ = ("ValidatePreFlightContractUseCase",)
