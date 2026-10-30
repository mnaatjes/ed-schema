"""Unit tests for DatamodelCodeGeneratorAdapter."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from ed_schema.adapters.driven.codegen import DatamodelCodeGeneratorAdapter
from ed_schema.core.domain.exceptions import SchemaCompilationError


def test_generate_dataclasses_success(tmp_path: Path) -> None:
    """Verifies generating Python dataclass file from JSON schema."""
    adapter = DatamodelCodeGeneratorAdapter()
    schema_file = tmp_path / "profile.json"
    output_file = tmp_path / "models" / "profile.py"

    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Profile",
        "description": "Commander profile response DTO.",
        "type": "object",
        "required": ["commander_id", "name"],
        "properties": {
            "commander_id": {"type": "string"},
            "name": {"type": "string"},
            "credits": {"type": "integer"},
        },
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    adapter.generate_dataclasses(
        schema_path=schema_file,
        output_file=output_file,
        class_prefix="Capi",
    )

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    assert "class CapiProfileDTO:" in content
    assert "commander_id: str" in content
    assert "name: str" in content
    assert "credits: int | None = None" in content
    assert "@dataclass(frozen=True)" in content

    # Assert generated code is syntactically valid Python AST
    tree = ast.parse(content)
    assert tree is not None


def test_generate_dataclasses_missing_schema_raises_compilation_error(tmp_path: Path) -> None:
    """Verifies compiling non-existent file raises SchemaCompilationError."""
    adapter = DatamodelCodeGeneratorAdapter()
    missing_file = tmp_path / "does_not_exist.json"
    output_file = tmp_path / "out.py"

    with pytest.raises(SchemaCompilationError, match="Schema file not found"):
        adapter.generate_dataclasses(
            schema_path=missing_file,
            output_file=output_file,
            class_prefix="Capi",
        )


def test_generate_dataclasses_corrupt_json_raises_compilation_error(tmp_path: Path) -> None:
    """Verifies malformed schema raises SchemaCompilationError."""
    adapter = DatamodelCodeGeneratorAdapter()
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{invalid", encoding="utf-8")
    output_file = tmp_path / "out.py"

    with pytest.raises(SchemaCompilationError, match="Failed reading schema document"):
        adapter.generate_dataclasses(
            schema_path=corrupt_file,
            output_file=output_file,
            class_prefix="Capi",
        )


def test_generate_dataclasses_sanitizes_dollar_sign_and_illegal_identifiers(
    tmp_path: Path,
) -> None:
    """Verifies $schemaRef, hyphens, and keywords are sanitized to valid Python identifiers."""
    adapter = DatamodelCodeGeneratorAdapter()
    schema_file = tmp_path / "journal-v1.0.json"
    output_file = tmp_path / "models" / "journal_v1_0.py"

    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Journal",
        "description": "EDDN Journal payload.",
        "type": "object",
        "required": ["$schemaRef", "import"],
        "properties": {
            "$schemaRef": {"type": "string"},
            "import": {"type": "string"},
            "kebab-case-prop": {"type": "integer"},
            "123numeric": {"type": "string"},
        },
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    adapter.generate_dataclasses(
        schema_path=schema_file,
        output_file=output_file,
        class_prefix="Eddn",
    )

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    # Assert valid class name
    assert "class EddnJournalDTO:" in content
    # Assert $schemaRef stripped to schemaRef
    assert "schemaRef: str" in content
    # Assert keyword 'import' suffixed to 'import_'
    assert "import_: str" in content
    # Assert kebab-case normalized to underscore
    assert "kebab_case_prop: int | None = None" in content
    # Assert numeric identifier prefixed
    assert "field_123numeric: str | None = None" in content

    # Assert generated Python code parses into valid AST with zero SyntaxError
    tree = ast.parse(content)
    assert tree is not None


def test_generate_dataclasses_recursive_nested_objects(tmp_path: Path) -> None:
    """Verifies recursive dataclass generation for nested objects."""
    adapter = DatamodelCodeGeneratorAdapter()
    schema_file = tmp_path / "nested.json"
    output_file = tmp_path / "models" / "nested.py"

    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Payload",
        "type": "object",
        "required": ["header", "message"],
        "properties": {
            "header": {
                "type": "object",
                "required": ["uploaderID"],
                "properties": {
                    "uploaderID": {"type": "string"},
                    "version": {"type": "integer"},
                },
            },
            "message": {
                "type": "object",
                "required": ["event"],
                "properties": {
                    "event": {"type": "string"},
                    "nested_sub": {
                        "type": "object",
                        "properties": {
                            "coord": {"type": "number"},
                        },
                    },
                },
            },
        },
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    adapter.generate_dataclasses(
        schema_path=schema_file,
        output_file=output_file,
        class_prefix="Capi",
    )

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    # Assert nested classes were generated
    assert "class CapiPayloadHeaderDTO:" in content
    assert "class CapiPayloadMessageDTO:" in content
    assert "class CapiPayloadMessageNestedSubDTO:" in content
    assert "class CapiPayloadDTO:" in content

    # Assert parent class references child classes
    assert "header: CapiPayloadHeaderDTO" in content
    assert "message: CapiPayloadMessageDTO" in content

    # Assert valid Python AST syntax
    tree = ast.parse(content)
    assert tree is not None


def test_generate_dataclasses_recursive_arrays(tmp_path: Path) -> None:
    """Verifies recursive dataclass generation for object array items."""
    adapter = DatamodelCodeGeneratorAdapter()
    schema_file = tmp_path / "batch.json"
    output_file = tmp_path / "models" / "batch.py"

    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "BatchEvent",
        "type": "object",
        "required": ["events"],
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["event_name"],
                    "properties": {
                        "event_name": {"type": "string"},
                        "event_id": {"type": "integer"},
                    },
                },
            },
        },
    }
    schema_file.write_text(json.dumps(schema_content), encoding="utf-8")

    adapter.generate_dataclasses(
        schema_path=schema_file,
        output_file=output_file,
        class_prefix="Inara",
    )

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    assert "class InaraBatchEventEventsItemDTO:" in content
    assert "class InaraBatchEventDTO:" in content
    assert "events: list[InaraBatchEventEventsItemDTO]" in content

    tree = ast.parse(content)
    assert tree is not None
