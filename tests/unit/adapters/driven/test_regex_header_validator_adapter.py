"""Unit tests for RegexHeaderValidatorAdapter."""

from __future__ import annotations

from ed_schema.adapters.driven.validator import RegexHeaderValidatorAdapter
from ed_schema.core.domain.models import HeaderContract, HeaderParameterContract


def test_validate_headers_empty_contract_and_empty_headers() -> None:
    """Verifies empty contract passes with empty headers."""
    adapter = RegexHeaderValidatorAdapter()
    contract = HeaderContract(parameters=())

    violations = adapter.validate_headers(contract=contract, headers={})
    assert violations == ()


def test_validate_headers_case_insensitivity() -> None:
    """Verifies headers match case-insensitively against contract parameters."""
    adapter = RegexHeaderValidatorAdapter()
    contract = HeaderContract(
        parameters=(
            HeaderParameterContract(name="Content-Type", required=True),
            HeaderParameterContract(name="X-API-Key", required=True),
        )
    )

    headers = {
        "content-type": "application/json",
        "X-api-KEY": "secret-12345",
    }

    violations = adapter.validate_headers(contract=contract, headers=headers)
    assert violations == ()


def test_validate_headers_missing_required_header() -> None:
    """Verifies missing required header produces clear violation message."""
    adapter = RegexHeaderValidatorAdapter()
    contract = HeaderContract(
        parameters=(
            HeaderParameterContract(name="Authorization", required=True),
            HeaderParameterContract(name="X-Optional-Client", required=False),
        )
    )

    violations = adapter.validate_headers(contract=contract, headers={})
    assert len(violations) == 1
    assert violations[0] == "Missing required header: 'authorization'"


def test_validate_headers_regex_matching_success() -> None:
    """Verifies regex pattern validates successfully."""
    adapter = RegexHeaderValidatorAdapter()
    contract = HeaderContract(
        parameters=(
            HeaderParameterContract(
                name="Authorization",
                required=True,
                regex_pattern=r"^Bearer\s+[A-Za-z0-9\-._~+/]+=*$",
            ),
        )
    )

    headers = {"Authorization": "Bearer abc123def456"}
    violations = adapter.validate_headers(contract=contract, headers=headers)
    assert violations == ()


def test_validate_headers_regex_matching_violation() -> None:
    """Verifies failing regex pattern produces violation."""
    adapter = RegexHeaderValidatorAdapter()
    contract = HeaderContract(
        parameters=(
            HeaderParameterContract(
                name="Authorization",
                required=True,
                regex_pattern=r"^Bearer\s+[A-Za-z0-9\-._~+/]+=*$",
            ),
        )
    )

    headers = {"Authorization": "Basic dXNlcjpwYXNz"}
    violations = adapter.validate_headers(contract=contract, headers=headers)
    assert len(violations) == 1
    assert "does not match required pattern" in violations[0]
