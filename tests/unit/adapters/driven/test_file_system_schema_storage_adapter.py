"""Unit tests for FileSystemSchemaStorageAdapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ed_schema.adapters.driven.storage import FileSystemSchemaStorageAdapter
from ed_schema.core.domain.exceptions import SchemaStorageError


def test_read_schema_document_success(tmp_path: Path) -> None:
    """Verifies reading a valid JSON schema file from disk."""
    adapter = FileSystemSchemaStorageAdapter()
    schema_file = tmp_path / "test_schema.json"
    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TestEvent",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    result = adapter.read_schema_document(schema_file)
    assert result == schema_content
    assert result["title"] == "TestEvent"


def test_read_schema_document_missing_file_raises_storage_error(tmp_path: Path) -> None:
    """Verifies that non-existent files raise SchemaStorageError."""
    adapter = FileSystemSchemaStorageAdapter()
    missing_file = tmp_path / "non_existent.json"

    with pytest.raises(SchemaStorageError, match="Schema file not found"):
        adapter.read_schema_document(missing_file)


def test_read_schema_document_invalid_json_raises_storage_error(tmp_path: Path) -> None:
    """Verifies that malformed JSON raises SchemaStorageError."""
    adapter = FileSystemSchemaStorageAdapter()
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{not valid json: true", encoding="utf-8")

    with pytest.raises(SchemaStorageError, match="Invalid JSON syntax"):
        adapter.read_schema_document(corrupt_file)


def test_read_schema_document_non_object_root_raises_storage_error(tmp_path: Path) -> None:
    """Verifies that JSON with non-dict root raises SchemaStorageError."""
    adapter = FileSystemSchemaStorageAdapter()
    array_file = tmp_path / "array.json"
    array_file.write_text('["item1", "item2"]', encoding="utf-8")

    with pytest.raises(SchemaStorageError, match="root must be a JSON object"):
        adapter.read_schema_document(array_file)


def test_list_schema_files_success(tmp_path: Path) -> None:
    """Verifies recursively enumerating schema files sorted alphabetically."""
    adapter = FileSystemSchemaStorageAdapter()
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()

    file_b = tmp_path / "b_schema.json"
    file_a = sub_dir / "a_schema.json"
    ignore_txt = tmp_path / "readme.txt"

    file_b.write_text("{}", encoding="utf-8")
    file_a.write_text("{}", encoding="utf-8")
    ignore_txt.write_text("text", encoding="utf-8")

    files = adapter.list_schema_files(tmp_path)
    assert len(files) == 2
    assert files == tuple(sorted([file_a.resolve(), file_b.resolve()]))


def test_list_schema_files_missing_directory_raises_storage_error(tmp_path: Path) -> None:
    """Verifies non-existent directory raises SchemaStorageError."""
    adapter = FileSystemSchemaStorageAdapter()
    missing_dir = tmp_path / "does_not_exist"

    with pytest.raises(SchemaStorageError, match="Schema directory does not exist"):
        adapter.list_schema_files(missing_dir)


def test_list_schema_files_file_as_dir_raises_storage_error(tmp_path: Path) -> None:
    """Verifies pointing list_schema_files at a file raises SchemaStorageError."""
    adapter = FileSystemSchemaStorageAdapter()
    dummy_file = tmp_path / "some_file.json"
    dummy_file.write_text("{}", encoding="utf-8")

    with pytest.raises(SchemaStorageError, match="is not a directory"):
        adapter.list_schema_files(dummy_file)
