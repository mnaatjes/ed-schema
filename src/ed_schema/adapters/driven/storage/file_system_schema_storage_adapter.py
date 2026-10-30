"""Filesystem-backed schema storage adapter implementing SchemaStoragePort."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ed_schema.core.domain.exceptions import SchemaStorageError
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


class FileSystemSchemaStorageAdapter(SchemaStoragePort):
    """Secondary SPI adapter for reading and listing schema files from disk."""

    def read_schema_document(self, file_path: Path) -> dict[str, Any]:
        """Reads and parses a raw JSON schema document from disk.

        Args:
            file_path: Resolved path to the target schema file.

        Returns:
            Parsed JSON schema dictionary.

        Raises:
            SchemaStorageError: If the file does not exist, cannot be read, or
                contains invalid JSON.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            msg = f"Schema file not found on disk: {file_path}"
            raise SchemaStorageError(msg) from exc
        except PermissionError as exc:
            msg = f"Permission denied reading schema file: {file_path}"
            raise SchemaStorageError(msg) from exc
        except UnicodeDecodeError as exc:
            msg = f"Schema file '{file_path}' is not valid UTF-8: {exc}"
            raise SchemaStorageError(msg) from exc
        except OSError as exc:
            msg = f"Operating system error reading schema file '{file_path}': {exc}"
            raise SchemaStorageError(msg) from exc

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON syntax in schema file '{file_path}': {exc}"
            raise SchemaStorageError(msg) from exc

        if not isinstance(parsed, dict):
            msg = (
                f"Schema document '{file_path}' root must be a JSON object, "
                f"got {type(parsed).__name__}"
            )
            raise SchemaStorageError(msg)

        return parsed

    def list_schema_files(self, schema_dir: Path) -> tuple[Path, ...]:
        """Enumerates all schema files within a target directory.

        Args:
            schema_dir: Root directory path to inspect.

        Returns:
            Sorted tuple of resolved Path objects.

        Raises:
            SchemaStorageError: If the directory does not exist or cannot be accessed.
        """
        if not schema_dir.exists():
            msg = f"Schema directory does not exist: {schema_dir}"
            raise SchemaStorageError(msg)

        if not schema_dir.is_dir():
            msg = f"Schema directory path is not a directory: {schema_dir}"
            raise SchemaStorageError(msg)

        try:
            files = [p.resolve() for p in schema_dir.rglob("*.json") if p.is_file()]
        except OSError as exc:
            msg = f"Failed listing schema files in directory '{schema_dir}': {exc}"
            raise SchemaStorageError(msg) from exc

        files.sort()
        return tuple(files)


__all__ = ("FileSystemSchemaStorageAdapter",)
