"""Bootstrap subpackage for dependency injection and composition root."""

from __future__ import annotations

from ed_schema.bootstrap.client_factory import create_schema_engine
from ed_schema.bootstrap.container import Container

__all__ = (
    "Container",
    "create_schema_engine",
)
