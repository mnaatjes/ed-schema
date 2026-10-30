"""Unit tests for SchemaEngine driving facade."""

from __future__ import annotations

from pathlib import Path

from ed_schema.adapters.driving.schema_engine import SchemaEngine
from ed_schema.core.domain.models import (
    EndpointContract,
    HeaderContract,
    HeaderParameterContract,
    SchemaDescriptor,
    SchemaKey,
)
from ed_schema.core.use_cases.compile_dataclasses_use_case import (
    CompileDataclassesUseCase,
)
from ed_schema.core.use_cases.register_schema_use_case import (
    RegisterSchemaUseCase,
)
from ed_schema.core.use_cases.validate_pre_flight_contract_use_case import (
    ValidatePreFlightContractUseCase,
)
from ed_schema.core.use_cases.verify_schema_parity_use_case import (
    VerifySchemaParityUseCase,
)
from tests.doubles.fake_schema_adapters import (
    FakeDatamodelGeneratorAdapter,
    FakeHeaderValidatorAdapter,
    FakeSchemaParserAdapter,
    FakeSchemaStorageAdapter,
)


def _build_test_engine(storage: FakeSchemaStorageAdapter | None = None) -> SchemaEngine:
    fake_storage = storage or FakeSchemaStorageAdapter()
    fake_header = FakeHeaderValidatorAdapter()
    fake_parser = FakeSchemaParserAdapter()
    fake_codegen = FakeDatamodelGeneratorAdapter()

    register_uc = RegisterSchemaUseCase(storage=fake_storage)
    validate_uc = ValidatePreFlightContractUseCase(
        registry_resolver=register_uc.resolve,
        header_validator=fake_header,
        schema_parser=fake_parser,
    )
    compile_uc = CompileDataclassesUseCase(
        storage=fake_storage,
        generator=fake_codegen,
    )
    parity_uc = VerifySchemaParityUseCase(storage=fake_storage)

    return SchemaEngine(
        register_use_case=register_uc,
        validate_use_case=validate_uc,
        compile_use_case=compile_uc,
        parity_use_case=parity_uc,
    )


def test_schema_engine_register_and_resolve() -> None:
    """Verifies storing and retrieving descriptors via SchemaEngine."""
    engine = _build_test_engine()
    key = SchemaKey(namespace="capi", endpoint="/profile")
    descriptor = SchemaDescriptor(key=key, schema_definition={"type": "object"})

    engine.register_descriptor(descriptor)
    resolved = engine.resolve_descriptor(key)

    assert resolved is not None
    assert resolved.key == key
    assert resolved.schema_definition == {"type": "object"}


def test_schema_engine_load_manifests() -> None:
    """Verifies batch loading manifests via SchemaEngine."""
    fake_storage = FakeSchemaStorageAdapter(
        schemas={Path("/schemas/profile.json"): {"title": "Profile"}}
    )
    engine = _build_test_engine(storage=fake_storage)

    class ManifestStub:
        name = "capi"
        schema_dir = Path("/schemas")
        endpoints = (
            EndpointContract(
                route="/profile",
                schema_file="profile.json",
            ),
        )

    loaded = engine.load_manifests([ManifestStub()])
    assert loaded == 1

    key = SchemaKey(namespace="capi", endpoint="/profile")
    resolved = engine.resolve_descriptor(key)
    assert resolved is not None


def test_schema_engine_validate_call_success() -> None:
    """Verifies pre-flight validation execution via SchemaEngine."""
    engine = _build_test_engine()
    key = SchemaKey(namespace="capi", endpoint="/profile")
    contract = HeaderContract(
        parameters=(HeaderParameterContract(name="authorization", required=True),)
    )
    descriptor = SchemaDescriptor(
        key=key,
        schema_definition={"type": "object"},
        header_contract=contract,
    )
    engine.register_descriptor(descriptor)

    result = engine.validate_call(
        key=key,
        headers={"authorization": "Bearer token"},
        payload={"id": "123"},
    )
    assert result.is_valid is True
    assert not result.has_errors


def test_schema_engine_compile_models(tmp_path: Path) -> None:
    """Verifies compiling models delegation via SchemaEngine."""
    schema_path = tmp_path / "schemas" / "event.json"
    output_dir = tmp_path / "models"
    fake_storage = FakeSchemaStorageAdapter(schemas={schema_path: {"title": "Event"}})
    engine = _build_test_engine(storage=fake_storage)

    compiled = engine.compile_models(
        schema_dir=tmp_path / "schemas",
        output_dir=output_dir,
        class_prefix="Capi",
    )
    assert len(compiled) == 1
    assert compiled[0] == output_dir / "event.py"


def test_schema_engine_verify_parity() -> None:
    """Verifies parity verification delegation via SchemaEngine."""
    fake_storage = FakeSchemaStorageAdapter(schemas={})
    engine = _build_test_engine(storage=fake_storage)

    report = engine.verify_parity(
        schema_dir=Path("/schemas"),
        models_dir=Path("/models"),
        namespace="capi",
        class_prefix="Capi",
    )
    assert report.is_synchronized is True
