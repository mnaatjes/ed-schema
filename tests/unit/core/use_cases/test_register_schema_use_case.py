"""Unit tests for RegisterSchemaUseCase (UC-01)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from ed_schema.core.domain.exceptions import SchemaRegistrationError
from ed_schema.core.domain.models import EndpointContract, SchemaDescriptor, SchemaKey
from ed_schema.core.use_cases.register_schema_use_case import (
    RegisterSchemaUseCase,
)
from tests.doubles.fake_schema_adapters import FakeSchemaStorageAdapter


@dataclass(frozen=True)
class DummyManifest:
    name: str
    schema_dir: Path
    endpoints: tuple[EndpointContract, ...]


class TestRegisterSchemaUseCase:
    """Tests for manifest loading and composite schema registration."""

    def test_register_and_resolve_single_descriptor(self) -> None:
        storage = FakeSchemaStorageAdapter()
        use_case = RegisterSchemaUseCase(storage=storage)

        key = SchemaKey(namespace="capi", endpoint="/profile")
        descriptor = SchemaDescriptor(key=key, schema_definition={"type": "object"})

        use_case.register(descriptor)
        resolved = use_case.resolve(key)

        assert resolved == descriptor

    def test_duplicate_registration_raises_collision_error(self) -> None:
        storage = FakeSchemaStorageAdapter()
        use_case = RegisterSchemaUseCase(storage=storage)

        key = SchemaKey(namespace="capi", endpoint="/profile")
        descriptor = SchemaDescriptor(key=key, schema_definition={"type": "object"})

        use_case.register(descriptor)
        with pytest.raises(SchemaRegistrationError, match="Collision"):
            use_case.register(descriptor)

    def test_execute_loads_manifest_endpoints(self) -> None:
        schema_path = Path("/mock/providers/capi/schemas/profile.json")
        storage = FakeSchemaStorageAdapter(
            schemas={schema_path: {"$schema": "Draft-07", "title": "Profile"}}
        )
        use_case = RegisterSchemaUseCase(storage=storage)

        manifest = DummyManifest(
            name="capi",
            schema_dir=Path("/mock/providers/capi/schemas"),
            endpoints=(EndpointContract(route="/profile", schema_file="profile.json"),),
        )

        count = use_case.execute([manifest])
        assert count == 1

        resolved = use_case.resolve(SchemaKey(namespace="capi", endpoint="/profile"))
        assert resolved is not None
        assert resolved.schema_definition["title"] == "Profile"

    def test_execute_with_missing_schema_raises_error(self) -> None:
        storage = FakeSchemaStorageAdapter(schemas={})
        use_case = RegisterSchemaUseCase(storage=storage)

        manifest = DummyManifest(
            name="capi",
            schema_dir=Path("/mock/schemas"),
            endpoints=(EndpointContract(route="/missing", schema_file="missing.json"),),
        )

        with pytest.raises(SchemaRegistrationError, match="Failed reading schema"):
            use_case.execute([manifest])
