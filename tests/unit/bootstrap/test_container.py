"""Unit tests for Container composition root and create_schema_engine factory."""

from __future__ import annotations

from ed_schema.adapters.driven.codegen import DatamodelCodeGeneratorAdapter
from ed_schema.adapters.driven.storage import FileSystemSchemaStorageAdapter
from ed_schema.adapters.driven.validator import (
    JsonSchemaParserAdapter,
    RegexHeaderValidatorAdapter,
)
from ed_schema.adapters.driving.schema_engine import SchemaEngine
from ed_schema.bootstrap.client_factory import create_schema_engine
from ed_schema.bootstrap.container import Container
from tests.doubles.fake_schema_adapters import (
    FakeDatamodelGeneratorAdapter,
    FakeHeaderValidatorAdapter,
    FakeSchemaParserAdapter,
    FakeSchemaStorageAdapter,
)


def test_container_default_resolution() -> None:
    """Verifies that Container resolves default production adapters."""
    container = Container()

    assert isinstance(container.resolve_storage(), FileSystemSchemaStorageAdapter)
    assert isinstance(container.resolve_header_validator(), RegexHeaderValidatorAdapter)
    assert isinstance(container.resolve_schema_parser(), JsonSchemaParserAdapter)
    assert isinstance(container.resolve_code_generator(), DatamodelCodeGeneratorAdapter)


def test_container_custom_adapter_injection() -> None:
    """Verifies that Container accepts injected test doubles."""
    fake_storage = FakeSchemaStorageAdapter()
    fake_header = FakeHeaderValidatorAdapter()
    fake_parser = FakeSchemaParserAdapter()
    fake_codegen = FakeDatamodelGeneratorAdapter()

    container = Container(
        storage_adapter=fake_storage,
        header_validator=fake_header,
        schema_parser=fake_parser,
        code_generator=fake_codegen,
    )

    assert container.resolve_storage() is fake_storage
    assert container.resolve_header_validator() is fake_header
    assert container.resolve_schema_parser() is fake_parser
    assert container.resolve_code_generator() is fake_codegen


def test_container_build_schema_engine() -> None:
    """Verifies building a fully wired SchemaEngine from Container."""
    container = Container()
    engine = container.build_schema_engine()
    assert isinstance(engine, SchemaEngine)


def test_create_schema_engine_factory() -> None:
    """Verifies create_schema_engine factory creates a functional SchemaEngine."""
    engine = create_schema_engine()
    assert isinstance(engine, SchemaEngine)
