"""Use case for compiling JSON schemas into typed Python dataclasses (UC-02)."""

from __future__ import annotations

from pathlib import Path

from ed_schema.core.domain.exceptions import SchemaCompilationError
from ed_schema.core.ports.driven.datamodel_generator_port import (
    DatamodelGeneratorPort,
)
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


class CompileDataclassesUseCase:
    """Orchestrates build-time compilation of JSON schemas into Python dataclasses."""

    def __init__(
        self,
        storage: SchemaStoragePort,
        generator: DatamodelGeneratorPort,
    ) -> None:
        self._storage = storage
        self._generator = generator

    def execute(
        self,
        schema_dir: Path,
        output_dir: Path,
        class_prefix: str,
    ) -> tuple[Path, ...]:
        """Discovers schemas and generates Python dataclasses."""
        if not class_prefix or not class_prefix.strip():
            raise SchemaCompilationError("class_prefix must be a non-empty string.")

        try:
            schema_files = self._storage.list_schema_files(schema_dir)
        except Exception as exc:
            raise SchemaCompilationError(
                f"Failed listing schema files in '{schema_dir}': {exc}"
            ) from exc

        if not schema_files:
            return ()

        compiled_files: list[Path] = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for schema_file in schema_files:
            if not schema_file.name.endswith(".json"):
                continue

            stem = schema_file.stem
            out_file = output_dir / f"{stem}.py"

            try:
                self._generator.generate_dataclasses(
                    schema_path=schema_file,
                    output_file=out_file,
                    class_prefix=class_prefix,
                )
            except Exception as exc:
                raise SchemaCompilationError(
                    f"Failed compiling schema '{schema_file}' to '{out_file}': {exc}"
                ) from exc

            compiled_files.append(out_file)

        return tuple(compiled_files)


__all__ = ("CompileDataclassesUseCase",)
