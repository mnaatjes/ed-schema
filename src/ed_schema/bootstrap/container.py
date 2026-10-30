"""Composition root wiring adapters and interactors into executable runtime services."""

from __future__ import annotations

from collections.abc import Callable

from ed_schema.adapters.driven.codegen import DatamodelCodeGeneratorAdapter
from ed_schema.adapters.driven.storage import FileSystemSchemaStorageAdapter
from ed_schema.adapters.driven.system_probe import OsSystemProbeAdapter
from ed_schema.adapters.driven.validator import (
    JsonSchemaParserAdapter,
    RegexHeaderValidatorAdapter,
)
from ed_schema.adapters.driving.cli_health import CliHealthAdapter
from ed_schema.adapters.driving.schema_engine import SchemaEngine
from ed_schema.core.domain.models import SchemaDescriptor, SchemaKey
from ed_schema.core.ports.driven.datamodel_generator_port import (
    DatamodelGeneratorPort,
)
from ed_schema.core.ports.driven.header_validator_port import HeaderValidatorPort
from ed_schema.core.ports.driven.probe_port import SystemProbePort
from ed_schema.core.ports.driven.schema_parser_port import SchemaParserPort
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort
from ed_schema.core.ports.driving.health_port import GetHealthPort
from ed_schema.core.use_cases.check_health import CheckHealthUseCase
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


class Container:
    """Dependency injection container and composition root for ed-schema."""

    def __init__(
        self,
        service_name: str = "schema-engine",
        storage_adapter: SchemaStoragePort | None = None,
        header_validator: HeaderValidatorPort | None = None,
        schema_parser: SchemaParserPort | None = None,
        code_generator: DatamodelGeneratorPort | None = None,
    ) -> None:
        self.service_name = service_name
        self._storage = storage_adapter or FileSystemSchemaStorageAdapter()
        self._header_validator = header_validator or RegexHeaderValidatorAdapter()
        self._schema_parser = schema_parser or JsonSchemaParserAdapter()
        self._code_generator = code_generator or DatamodelCodeGeneratorAdapter()

    # -------------------------------------------------------------------------
    # Driven Adapter Resolvers
    # -------------------------------------------------------------------------
    def resolve_storage(self) -> SchemaStoragePort:
        """Resolves storage secondary SPI adapter."""
        return self._storage

    def resolve_header_validator(self) -> HeaderValidatorPort:
        """Resolves header validator secondary SPI adapter."""
        return self._header_validator

    def resolve_schema_parser(self) -> SchemaParserPort:
        """Resolves schema parser secondary SPI adapter."""
        return self._schema_parser

    def resolve_code_generator(self) -> DatamodelGeneratorPort:
        """Resolves datamodel code generator secondary SPI adapter."""
        return self._code_generator

    def build_system_probe(self) -> SystemProbePort:
        """Instantiates system probe driven adapter."""
        return OsSystemProbeAdapter()

    # -------------------------------------------------------------------------
    # Interactor Builders
    # -------------------------------------------------------------------------
    def build_register_schema_use_case(self) -> RegisterSchemaUseCase:
        """Builds RegisterSchemaUseCase with wired storage adapter."""
        return RegisterSchemaUseCase(storage=self.resolve_storage())

    def build_compile_dataclasses_use_case(self) -> CompileDataclassesUseCase:
        """Builds CompileDataclassesUseCase with wired storage and codegen adapters."""
        return CompileDataclassesUseCase(
            storage=self.resolve_storage(),
            generator=self.resolve_code_generator(),
        )

    def build_verify_schema_parity_use_case(self) -> VerifySchemaParityUseCase:
        """Builds VerifySchemaParityUseCase with wired storage adapter."""
        return VerifySchemaParityUseCase(storage=self.resolve_storage())

    def build_validate_pre_flight_contract_use_case(
        self,
        registry_resolver: Callable[[SchemaKey], SchemaDescriptor | None],
    ) -> ValidatePreFlightContractUseCase:
        """Builds ValidatePreFlightContractUseCase with wired validators and resolver."""
        return ValidatePreFlightContractUseCase(
            registry_resolver=registry_resolver,
            header_validator=self.resolve_header_validator(),
            schema_parser=self.resolve_schema_parser(),
        )

    def build_health_use_case(self) -> GetHealthPort:
        """Instantiates health use case interactor with injected driven probe."""
        probe = self.build_system_probe()
        return CheckHealthUseCase(probe=probe, service_name=self.service_name)

    # -------------------------------------------------------------------------
    # Driving Adapter Builders
    # -------------------------------------------------------------------------
    def build_cli_health_adapter(self) -> CliHealthAdapter:
        """Instantiates driving health adapter with injected use case."""
        return CliHealthAdapter(health_service=self.build_health_use_case())

    def build_schema_engine(self) -> SchemaEngine:
        """Builds unified SchemaEngine driving facade with all wired use cases."""
        register_uc = self.build_register_schema_use_case()
        validate_uc = self.build_validate_pre_flight_contract_use_case(
            registry_resolver=register_uc.resolve,
        )
        compile_uc = self.build_compile_dataclasses_use_case()
        parity_uc = self.build_verify_schema_parity_use_case()

        return SchemaEngine(
            register_use_case=register_uc,
            validate_use_case=validate_uc,
            compile_use_case=compile_uc,
            parity_use_case=parity_uc,
        )


__all__ = ("Container",)
