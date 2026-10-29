"""Unit tests for ValidatePreFlightContractUseCase (UC-04)."""

from __future__ import annotations

from ed_schema.core.domain.models import (
    HeaderContract,
    HeaderParameterContract,
    SchemaDescriptor,
    SchemaKey,
    SchemaValidationError,
)
from ed_schema.core.use_cases.validate_pre_flight_contract_use_case import (
    ValidatePreFlightContractUseCase,
)
from tests.doubles.fake_schema_adapters import (
    FakeHeaderValidatorAdapter,
    FakeSchemaParserAdapter,
)


class TestValidatePreFlightContractUseCase:
    """Tests for composite pre-flight validation."""

    def test_valid_pre_flight_call(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        header_contract = HeaderContract(
            parameters=(HeaderParameterContract(name="authorization", required=True),)
        )
        descriptor = SchemaDescriptor(
            key=key,
            schema_definition={"type": "object"},
            header_contract=header_contract,
        )

        registry = {key: descriptor}
        header_val = FakeHeaderValidatorAdapter(errors=())
        schema_parser = FakeSchemaParserAdapter(errors=())

        use_case = ValidatePreFlightContractUseCase(
            registry_resolver=registry.get,
            header_validator=header_val,
            schema_parser=schema_parser,
        )

        result = use_case.execute(
            key=key,
            headers={"authorization": "Bearer token123"},
            payload={"commander": "Test"},
        )

        assert result.is_valid is True
        assert result.has_errors is False

    def test_unregistered_key_fails_validation(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/unregistered")
        registry: dict[SchemaKey, SchemaDescriptor] = {}

        header_val = FakeHeaderValidatorAdapter()
        schema_parser = FakeSchemaParserAdapter()

        use_case = ValidatePreFlightContractUseCase(
            registry_resolver=registry.get,
            header_validator=header_val,
            schema_parser=schema_parser,
        )

        result = use_case.execute(key=key, headers={})

        assert result.is_valid is False
        assert len(result.header_errors) == 1
        assert "Unregistered" in result.header_errors[0]

    def test_header_and_payload_errors_aggregated(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        descriptor = SchemaDescriptor(
            key=key,
            schema_definition={"type": "object"},
            header_contract=HeaderContract(),
        )

        registry = {key: descriptor}
        header_val = FakeHeaderValidatorAdapter(errors=("Missing Authorization",))
        err = SchemaValidationError(path="name", message="missing", validator="required")
        schema_parser = FakeSchemaParserAdapter(errors=(err,))

        use_case = ValidatePreFlightContractUseCase(
            registry_resolver=registry.get,
            header_validator=header_val,
            schema_parser=schema_parser,
        )

        result = use_case.execute(
            key=key,
            headers={},
            payload={"bad": "data"},
        )

        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.header_errors) == 1
        assert len(result.payload_errors) == 1
