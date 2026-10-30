"""Use case for loading manifests and registering schemas (UC-01)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ed_schema.core.domain.exceptions import SchemaRegistrationError
from ed_schema.core.domain.models import EndpointContract, SchemaDescriptor, SchemaKey
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


class RegisterSchemaUseCase:
    """Orchestrates ingestion of provider manifests into the in-memory registry."""

    def __init__(self, storage: SchemaStoragePort) -> None:
        self._storage = storage
        self._registry: dict[SchemaKey, SchemaDescriptor] = {}

    def register(self, descriptor: SchemaDescriptor) -> None:
        """Stores a schema descriptor indexed by its SchemaKey."""
        if descriptor.key in self._registry:
            raise SchemaRegistrationError(
                f"Collision: SchemaKey '{descriptor.key}' is already registered."
            )
        self._registry[descriptor.key] = descriptor

    def resolve(self, key: SchemaKey) -> SchemaDescriptor | None:
        """Resolves a registered schema descriptor in microseconds."""
        return self._registry.get(key)

    def execute(self, manifests: Sequence[Any]) -> int:
        """Batch loads schemas across provider manifest declarations."""
        registered_count = 0

        for manifest in manifests:
            namespace = getattr(manifest, "name", None)
            schema_dir = getattr(manifest, "schema_dir", None)
            endpoints = getattr(manifest, "endpoints", ())

            if not namespace or not isinstance(namespace, str):
                raise SchemaRegistrationError(
                    f"Manifest must declare a valid 'name' string: {manifest}"
                )
            if not schema_dir:
                raise SchemaRegistrationError(f"Manifest '{namespace}' must declare 'schema_dir'.")

            schema_dir_path = Path(schema_dir)

            for endpoint in endpoints:
                if not isinstance(endpoint, EndpointContract):
                    msg = (
                        f"Manifest '{namespace}' endpoints must be "
                        f"EndpointContract instances: {endpoint}"
                    )
                    raise SchemaRegistrationError(msg)

                key = SchemaKey(
                    namespace=namespace,
                    endpoint=endpoint.route,
                    discriminator_field=endpoint.discriminator_field,
                    discriminator_value=endpoint.discriminator_value,
                )

                file_path = schema_dir_path / endpoint.schema_file
                try:
                    schema_def = self._storage.read_schema_document(file_path)
                except Exception as exc:
                    err_msg = (
                        f"Failed reading schema document '{file_path}' "
                        f"for namespace '{namespace}': {exc}"
                    )
                    raise SchemaRegistrationError(err_msg) from exc

                descriptor = SchemaDescriptor(
                    key=key,
                    schema_definition=schema_def,
                    model_cls=endpoint.model_cls,
                    header_contract=endpoint.header_contract,
                )
                self.register(descriptor)
                registered_count += 1

        return registered_count


__all__ = ("RegisterSchemaUseCase",)
