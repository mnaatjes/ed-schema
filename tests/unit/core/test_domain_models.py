"""Unit tests for ed-schema core domain models and value objects."""

from __future__ import annotations

import pytest

from ed_schema.core.domain.exceptions import (
    ContractViolationError,
    DomainError,
    DomainValidationError,
    SchemaCompilationError,
    SchemaParityError,
    SchemaRegistrationError,
)
from ed_schema.core.domain.models import (
    EndpointContract,
    HeaderContract,
    HeaderParameterContract,
    ParityMismatch,
    ParityReport,
    SchemaDescriptor,
    SchemaKey,
    SchemaValidationError,
    ValidationResult,
)


class TestSchemaKey:
    """Tests for SchemaKey 4-tuple composite key identifier."""

    def test_valid_minimal_key(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        assert key.namespace == "capi"
        assert key.endpoint == "/profile"
        assert key.discriminator_field is None
        assert key.discriminator_value is None

    def test_valid_discriminator_key(self) -> None:
        key = SchemaKey(
            namespace="eddn",
            endpoint="/upload/",
            discriminator_field="$schemaRef",
            discriminator_value="commodity/3",
        )
        assert key.discriminator_field == "$schemaRef"
        assert key.discriminator_value == "commodity/3"

    def test_empty_namespace_raises_validation_error(self) -> None:
        with pytest.raises(DomainValidationError, match="namespace"):
            SchemaKey(namespace="", endpoint="/profile")

    def test_endpoint_missing_leading_slash_raises_validation_error(self) -> None:
        with pytest.raises(DomainValidationError, match="must begin with '/'"):
            SchemaKey(namespace="capi", endpoint="profile")

    def test_half_specified_discriminator_raises_validation_error(self) -> None:
        with pytest.raises(DomainValidationError, match="both be set or both be None"):
            SchemaKey(
                namespace="inara",
                endpoint="/inapi/v1/",
                discriminator_field="eventName",
                discriminator_value=None,
            )

    def test_immutability(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        with pytest.raises(AttributeError):
            key.namespace = "other"  # type: ignore[misc]


class TestHeaderContract:
    """Tests for HeaderParameterContract and HeaderContract."""

    def test_header_name_lowercasing(self) -> None:
        param = HeaderParameterContract(name="  Content-Type  ")
        assert param.name == "content-type"

    def test_empty_header_name_raises_error(self) -> None:
        with pytest.raises(DomainValidationError, match="cannot be empty"):
            HeaderParameterContract(name="")

    def test_header_contract_lookup(self) -> None:
        p1 = HeaderParameterContract(name="authorization", required=True)
        p2 = HeaderParameterContract(name="content-type", required=True)
        contract = HeaderContract(parameters=(p1, p2))

        assert contract.get("AUTHORIZATION") == p1
        assert contract.get("Content-Type") == p2
        assert contract.get("X-Unknown") is None


class TestEndpointContract:
    """Tests for EndpointContract manifest declarations."""

    def test_valid_endpoint_contract(self) -> None:
        ep = EndpointContract(route="/market", schema_file="market.json")
        assert ep.route == "/market"
        assert ep.schema_file == "market.json"

    def test_invalid_route_raises_error(self) -> None:
        with pytest.raises(DomainValidationError, match="must start with '/'"):
            EndpointContract(route="market", schema_file="market.json")

    def test_non_json_schema_file_raises_error(self) -> None:
        with pytest.raises(DomainValidationError, match="must be a .json file"):
            EndpointContract(route="/market", schema_file="market.yaml")


class TestSchemaDescriptor:
    """Tests for SchemaDescriptor contract bundle."""

    def test_valid_descriptor(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        desc = SchemaDescriptor(key=key, schema_definition={"type": "object"})
        assert desc.key == key
        assert desc.schema_definition == {"type": "object"}

    def test_invalid_schema_definition_type_raises_error(self) -> None:
        key = SchemaKey(namespace="capi", endpoint="/profile")
        with pytest.raises(DomainValidationError, match="must be a dict"):
            SchemaDescriptor(key=key, schema_definition="invalid")  # type: ignore[arg-type]


class TestValidationResult:
    """Tests for ValidationResult and SchemaValidationError."""

    def test_successful_result(self) -> None:
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.has_errors is False

    def test_result_with_errors(self) -> None:
        err = SchemaValidationError(path="user.id", message="required", validator="required")
        result = ValidationResult(
            is_valid=False,
            payload_errors=(err,),
            header_errors=("missing Authorization",),
        )
        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.payload_errors) == 1
        assert len(result.header_errors) == 1


class TestParityReport:
    """Tests for ParityReport and ParityMismatch."""

    def test_synchronized_report(self) -> None:
        report = ParityReport(namespace="capi", is_synchronized=True)
        assert report.is_synchronized is True
        assert len(report.mismatches) == 0

    def test_mismatched_report(self) -> None:
        mismatch = ParityMismatch(
            entity_name="CapiProfileDTO",
            attribute_name="commander_id",
            mismatch_type="MISSING_FIELD",
            description="Field present in schema but absent in DTO",
        )
        report = ParityReport(
            namespace="capi",
            is_synchronized=False,
            mismatches=(mismatch,),
        )
        assert report.is_synchronized is False
        assert len(report.mismatches) == 1


class TestDomainExceptionHierarchy:
    """Tests that domain exceptions adhere to Hexagonal DomainError hierarchy."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            DomainValidationError,
            SchemaRegistrationError,
            ContractViolationError,
            SchemaParityError,
            SchemaCompilationError,
        ],
    )
    def test_exception_inherits_from_domain_error(self, exc_cls: type[Exception]) -> None:
        assert issubclass(exc_cls, DomainError)
