"""Driven port contract for schema file persistence access."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ed_schema.core.ports.base import DrivenPort


@runtime_checkable
class SchemaStoragePort(DrivenPort, Protocol):
    """Secondary SPI for reading schema documents from disk."""

    def read_schema_document(self, file_path: Path) -> dict[str, Any]:
        """Reads and parses a raw JSON schema document from disk."""
        ...

    def list_schema_files(self, schema_dir: Path) -> tuple[Path, ...]:
        """Enumerates all schema files within a target directory."""
        ...


__all__ = ["SchemaStoragePort"]
