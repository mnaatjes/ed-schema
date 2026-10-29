"""Driven port contract for code generator engine adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ed_schema.core.ports.base import DrivenPort


@runtime_checkable
class DatamodelGeneratorPort(DrivenPort, Protocol):
    """Secondary SPI for compiling schema files to Python dataclass code."""

    def generate_dataclasses(
        self,
        schema_path: Path,
        output_file: Path,
        class_prefix: str,
    ) -> None:
        """Generates a typed Python dataclass file from a JSON schema."""
        ...


__all__ = ["DatamodelGeneratorPort"]
