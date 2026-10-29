"""Driving port contract for schema registration and lookup."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from ed_schema.core.domain.models import SchemaDescriptor, SchemaKey
from ed_schema.core.ports.base import DrivingPort


@runtime_checkable
class SchemaRegistryPort(DrivingPort, Protocol):
    """Primary port for managing the multi-namespace composite schema registry."""

    def register(self, descriptor: SchemaDescriptor) -> None:
        """Stores a schema descriptor indexed by its SchemaKey."""
        ...

    def resolve(self, key: SchemaKey) -> SchemaDescriptor | None:
        """Resolves a registered schema descriptor in microseconds."""
        ...

    def load_from_manifests(self, manifests: Sequence[Any]) -> int:
        """Batch loads schemas across provider manifest declarations."""
        ...


__all__ = ["SchemaRegistryPort"]
