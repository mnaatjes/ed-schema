"""Driving port contract for in-process AST schema parity verification."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ed_schema.core.domain.models import ParityReport
from ed_schema.core.ports.base import DrivingPort


@runtime_checkable
class ParityVerifierPort(DrivingPort, Protocol):
    """Primary port for verifying structural parity between schemas and DTOs."""

    def verify_parity(
        self,
        schema_dir: Path,
        models_dir: Path,
        namespace: str,
        class_prefix: str,
    ) -> ParityReport:
        """Verifies that generated Python models identically match JSON schemas."""
        ...


__all__ = ["ParityVerifierPort"]
