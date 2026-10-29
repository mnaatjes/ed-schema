"""Unit tests for VerifySchemaParityUseCase (UC-03)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ed_schema.core.domain.exceptions import SchemaParityError
from ed_schema.core.use_cases.verify_schema_parity_use_case import (
    VerifySchemaParityUseCase,
)
from tests.doubles.fake_schema_adapters import FakeSchemaStorageAdapter


class TestVerifySchemaParityUseCase:
    """Tests for in-process AST parity verification."""

    def test_synchronized_models(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / "schemas"
        models_dir = tmp_path / "models"
        schema_dir.mkdir()
        models_dir.mkdir()

        schema_file = schema_dir / "profile.json"
        storage = FakeSchemaStorageAdapter(
            schemas={
                schema_file: {
                    "properties": {"commander_id": {"type": "string"}},
                    "required": ["commander_id"],
                }
            }
        )

        model_file = models_dir / "profile.py"
        model_file.write_text(
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True)\n"
            "class CapiProfileDTO:\n"
            "    commander_id: str\n",
            encoding="utf-8",
        )

        use_case = VerifySchemaParityUseCase(storage=storage)
        report = use_case.execute(
            schema_dir=schema_dir,
            models_dir=models_dir,
            namespace="capi",
            class_prefix="Capi",
        )

        assert report.is_synchronized is True
        assert len(report.mismatches) == 0

    def test_missing_required_field_detected(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / "schemas"
        models_dir = tmp_path / "models"
        schema_dir.mkdir()
        models_dir.mkdir()

        schema_file = schema_dir / "profile.json"
        storage = FakeSchemaStorageAdapter(
            schemas={
                schema_file: {
                    "properties": {
                        "commander_id": {"type": "string"},
                        "credits": {"type": "integer"},
                    },
                    "required": ["commander_id", "credits"],
                }
            }
        )

        model_file = models_dir / "profile.py"
        model_file.write_text(
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True)\n"
            "class CapiProfileDTO:\n"
            "    commander_id: str\n",
            encoding="utf-8",
        )

        use_case = VerifySchemaParityUseCase(storage=storage)
        report = use_case.execute(
            schema_dir=schema_dir,
            models_dir=models_dir,
            namespace="capi",
            class_prefix="Capi",
        )

        assert report.is_synchronized is False
        assert len(report.mismatches) == 1
        assert report.mismatches[0].attribute_name == "credits"

    def test_missing_model_file_detected(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / "schemas"
        models_dir = tmp_path / "models"
        schema_dir.mkdir()
        models_dir.mkdir()

        schema_file = schema_dir / "profile.json"
        storage = FakeSchemaStorageAdapter(schemas={schema_file: {"properties": {}}})

        use_case = VerifySchemaParityUseCase(storage=storage)
        report = use_case.execute(
            schema_dir=schema_dir,
            models_dir=models_dir,
            namespace="capi",
            class_prefix="Capi",
        )

        assert report.is_synchronized is False
        assert report.mismatches[0].mismatch_type == "MISSING_FILE"

    def test_empty_namespace_raises_error(self, tmp_path: Path) -> None:
        storage = FakeSchemaStorageAdapter()
        use_case = VerifySchemaParityUseCase(storage=storage)

        with pytest.raises(SchemaParityError, match="namespace"):
            use_case.execute(
                schema_dir=tmp_path,
                models_dir=tmp_path,
                namespace="",
                class_prefix="Capi",
            )
