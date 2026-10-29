"""Unit tests for CompileDataclassesUseCase (UC-02)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ed_schema.core.domain.exceptions import SchemaCompilationError
from ed_schema.core.use_cases.compile_dataclasses_use_case import (
    CompileDataclassesUseCase,
)
from tests.doubles.fake_schema_adapters import (
    FakeDatamodelGeneratorAdapter,
    FakeSchemaStorageAdapter,
)


class TestCompileDataclassesUseCase:
    """Tests for programmatic build-time compilation."""

    def test_successful_compilation(self, tmp_path: Path) -> None:
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "models"
        schema_file = schema_dir / "profile.json"

        storage = FakeSchemaStorageAdapter(schemas={schema_file: {"type": "object"}})
        generator = FakeDatamodelGeneratorAdapter()
        use_case = CompileDataclassesUseCase(storage=storage, generator=generator)

        compiled = use_case.execute(
            schema_dir=schema_dir,
            output_dir=output_dir,
            class_prefix="Capi",
        )

        assert len(compiled) == 1
        assert compiled[0] == output_dir / "profile.py"
        assert len(generator.generated) == 1
        assert generator.generated[0][2] == "Capi"

    def test_empty_class_prefix_raises_error(self, tmp_path: Path) -> None:
        storage = FakeSchemaStorageAdapter()
        generator = FakeDatamodelGeneratorAdapter()
        use_case = CompileDataclassesUseCase(storage=storage, generator=generator)

        with pytest.raises(SchemaCompilationError, match="class_prefix"):
            use_case.execute(
                schema_dir=tmp_path,
                output_dir=tmp_path / "out",
                class_prefix="",
            )

    def test_no_schemas_returns_empty_tuple(self, tmp_path: Path) -> None:
        storage = FakeSchemaStorageAdapter(schemas={})
        generator = FakeDatamodelGeneratorAdapter()
        use_case = CompileDataclassesUseCase(storage=storage, generator=generator)

        compiled = use_case.execute(
            schema_dir=tmp_path / "empty",
            output_dir=tmp_path / "out",
            class_prefix="Test",
        )
        assert compiled == ()
