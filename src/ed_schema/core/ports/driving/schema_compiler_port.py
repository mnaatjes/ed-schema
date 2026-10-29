"""Driving port contract for programmatic build-time model compilation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ed_schema.core.ports.base import DrivingPort


@runtime_checkable
class SchemaCompilerPort(DrivingPort, Protocol):
    """Primary port for compiling JSON Schemas into static Python dataclasses."""

    def compile_models(
        self,
        schema_dir: Path,
        output_dir: Path,
        class_prefix: str,
    ) -> tuple[Path, ...]:
        """Compiles all JSON schemas in schema_dir into typed Python models."""
        ...


__all__ = ["SchemaCompilerPort"]
