"""Unit tests for JsonSchemaParserAdapter."""

from __future__ import annotations

from ed_schema.adapters.driven.validator import JsonSchemaParserAdapter


def test_validate_payload_valid_object_returns_no_errors() -> None:
    """Verifies valid dictionary payload returns empty error tuple."""
    adapter = JsonSchemaParserAdapter()
    schema = {
        "type": "object",
        "required": ["timestamp", "commanderName"],
        "properties": {
            "timestamp": {"type": "string"},
            "commanderName": {"type": "string"},
            "credits": {"type": "integer"},
        },
    }
    payload = {
        "timestamp": "3301-01-01T12:00:00Z",
        "commanderName": "Jameson",
        "credits": 1000000,
    }

    errors = adapter.validate_payload(schema, payload)
    assert errors == ()


def test_validate_payload_missing_required_property() -> None:
    """Verifies missing required property returns SchemaValidationError."""
    adapter = JsonSchemaParserAdapter()
    schema = {
        "type": "object",
        "required": ["commanderName"],
        "properties": {
            "commanderName": {"type": "string"},
        },
    }
    payload = {}

    errors = adapter.validate_payload(schema, payload)
    assert len(errors) == 1
    assert errors[0].validator == "required"
    assert "commanderName" in errors[0].message


def test_validate_payload_type_mismatch() -> None:
    """Verifies property type mismatch returns SchemaValidationError."""
    adapter = JsonSchemaParserAdapter()
    schema = {
        "type": "object",
        "properties": {
            "count": {"type": "integer"},
        },
    }
    payload = {"count": "not_an_integer"}

    errors = adapter.validate_payload(schema, payload)
    assert len(errors) == 1
    assert errors[0].validator == "type"
    assert "count" in errors[0].path


def test_validate_payload_nested_array_validation() -> None:
    """Verifies nested array items are checked."""
    adapter = JsonSchemaParserAdapter()
    schema = {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["eventName"],
                    "properties": {"eventName": {"type": "string"}},
                },
            }
        },
    }
    payload = {
        "events": [
            {"eventName": "Scan"},
            {},  # Missing eventName
        ]
    }

    errors = adapter.validate_payload(schema, payload)
    assert len(errors) == 1
    assert errors[0].validator == "required"
