"""Factory functions for creating production-ready SchemaEngine facades."""

from __future__ import annotations

from ed_schema.adapters.driving.schema_engine import SchemaEngine
from ed_schema.bootstrap.container import Container
from ed_schema.core.ports.driven.datamodel_generator_port import (
    DatamodelGeneratorPort,
)
from ed_schema.core.ports.driven.header_validator_port import HeaderValidatorPort
from ed_schema.core.ports.driven.schema_parser_port import SchemaParserPort
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


def create_schema_engine(
    *,
    storage_adapter: SchemaStoragePort | None = None,
    header_validator: HeaderValidatorPort | None = None,
    schema_parser: SchemaParserPort | None = None,
    code_generator: DatamodelGeneratorPort | None = None,
) -> SchemaEngine:
    """Instantiates a fully wired, production-ready SchemaEngine driving facade.

    Args:
        storage_adapter: Optional custom storage adapter implementation.
        header_validator: Optional custom header validator adapter implementation.
        schema_parser: Optional custom JSON schema parser adapter implementation.
        code_generator: Optional custom datamodel code generator adapter implementation.

    Returns:
        Configured SchemaEngine driving facade instance.
    """
    container = Container(
        storage_adapter=storage_adapter,
        header_validator=header_validator,
        schema_parser=schema_parser,
        code_generator=code_generator,
    )
    return container.build_schema_engine()


__all__ = ("create_schema_engine",)
