"""In-memory test doubles for ed-schema driven ports."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ed_schema.core.domain.models import HeaderContract, SchemaValidationError
from ed_schema.core.ports.driven.datamodel_generator_port import (
    DatamodelGeneratorPort,
)
from ed_schema.core.ports.driven.header_validator_port import HeaderValidatorPort
from ed_schema.core.ports.driven.schema_parser_port import SchemaParserPort
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


class FakeSchemaStorageAdapter(SchemaStoragePort):
    """In-memory fake storage adapter for schema files."""

    def __init__(self, schemas: dict[Path, dict[str, Any]] | None = None) -> None:
        self._schemas: dict[Path, dict[str, Any]] = schemas or {}

    def read_schema_document(self, file_path: Path) -> dict[str, Any]:
        if file_path not in self._schemas:
            raise FileNotFoundError(f"Schema file not found in fake storage: {file_path}")
        return self._schemas[file_path]

    def list_schema_files(self, schema_dir: Path) -> tuple[Path, ...]:
        return tuple(p for p in self._schemas if str(p).startswith(str(schema_dir)))


class FakeSchemaParserAdapter(SchemaParserPort):
    """In-memory fake schema parser and validator adapter."""

    def __init__(self, errors: tuple[SchemaValidationError, ...] = ()) -> None:
        self._errors = errors

    def validate_payload(
        self,
        schema_definition: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[SchemaValidationError, ...]:
        return self._errors


class FakeDatamodelGeneratorAdapter(DatamodelGeneratorPort):
    """In-memory fake datamodel generator adapter."""

    def __init__(self) -> None:
        self.generated: list[tuple[Path, Path, str]] = []

    def generate_dataclasses(
        self,
        schema_path: Path,
        output_file: Path,
        class_prefix: str,
    ) -> None:
        self.generated.append((schema_path, output_file, class_prefix))


class FakeHeaderValidatorAdapter(HeaderValidatorPort):
    """In-memory fake header validator adapter."""

    def __init__(self, errors: tuple[str, ...] = ()) -> None:
        self._errors = errors

    def validate_headers(
        self,
        contract: HeaderContract,
        headers: Mapping[str, str],
    ) -> tuple[str, ...]:
        return self._errors


__all__ = [
    "FakeSchemaStorageAdapter",
    "FakeSchemaParserAdapter",
    "FakeDatamodelGeneratorAdapter",
    "FakeHeaderValidatorAdapter",
]
