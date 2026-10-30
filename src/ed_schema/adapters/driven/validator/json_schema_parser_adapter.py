"""JSON Schema parsing and validation adapter implementing SchemaParserPort."""

from __future__ import annotations

import re
from typing import Any

from ed_schema.core.domain.models import SchemaValidationError
from ed_schema.core.ports.driven.schema_parser_port import SchemaParserPort

try:
    import jsonschema  # type: ignore[import-untyped]
    from jsonschema.exceptions import (  # type: ignore[import-untyped]
        ValidationError as JsonschemaValidationError,
    )

    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False
    JsonschemaValidationError = Exception  # type: ignore[assignment,misc]


class JsonSchemaParserAdapter(SchemaParserPort):
    """Secondary SPI adapter for JSON schema syntax checking and payload validation."""

    def __init__(self) -> None:
        self._has_engine = _HAS_JSONSCHEMA

    def validate_payload(
        self,
        schema_definition: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[SchemaValidationError, ...]:
        """Validates payload against schema_definition, returning any violations.

        Args:
            schema_definition: Raw JSON Schema specification dictionary.
            payload: Data payload dictionary to validate.

        Returns:
            Tuple of SchemaValidationError domain entities.
        """
        if self._has_engine:
            return self._validate_with_jsonschema(schema_definition, payload)
        return self._validate_with_fallback(schema_definition, payload)

    def _validate_with_jsonschema(
        self,
        schema_definition: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[SchemaValidationError, ...]:
        """Validates payload using full Draft-07 / Draft 2020-12 jsonschema engine."""
        validator_cls = jsonschema.Draft202012Validator
        if schema_definition.get("$schema", "").endswith("draft-07/schema#"):
            validator_cls = jsonschema.Draft7Validator

        try:
            validator = validator_cls(schema_definition)
        except Exception:
            # Fallback to standard validator if custom draft resolution fails
            validator = jsonschema.Draft202012Validator(schema_definition)

        errors: list[SchemaValidationError] = []
        for err in validator.iter_errors(payload):
            path_segments = [str(elem) for elem in err.path]
            json_path = "$." + ".".join(path_segments) if path_segments else "$"
            rule = str(err.validator) if err.validator else "schema"
            errors.append(
                SchemaValidationError(
                    path=json_path,
                    message=err.message,
                    validator=rule,
                )
            )

        return tuple(errors)

    def _validate_with_fallback(
        self,
        schema_definition: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[SchemaValidationError, ...]:
        """Built-in structural validator verifying type, required fields, and basic constraints."""
        errors: list[SchemaValidationError] = []
        self._validate_node(schema_definition, payload, path="$", errors=errors)
        return tuple(errors)

    def _validate_node(
        self,
        subschema: dict[str, Any],
        instance: Any,
        path: str,
        errors: list[SchemaValidationError],
    ) -> None:
        """Recursively checks instance against subschema constraints."""
        expected_type = subschema.get("type")
        if expected_type:
            valid_types = (
                (expected_type,) if isinstance(expected_type, str) else tuple(expected_type)
            )
            type_map: dict[str, tuple[type[Any], ...] | type[Any]] = {
                "object": dict,
                "array": list,
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "null": type(None),
            }
            allowed_py_types: list[type[Any]] = []
            for t in valid_types:
                mapped = type_map.get(t)
                if mapped:
                    if isinstance(mapped, tuple):
                        allowed_py_types.extend(mapped)
                    else:
                        allowed_py_types.append(mapped)

            # Note: bool is subclass of int in Python; ensure strict separation
            if "integer" in valid_types and isinstance(instance, bool):
                errors.append(
                    SchemaValidationError(
                        path=path,
                        message=f"Expected integer, got boolean at {path}",
                        validator="type",
                    )
                )
                return

            if allowed_py_types and not any(isinstance(instance, pt) for pt in allowed_py_types):
                msg = f"Expected type {expected_type}, got {type(instance).__name__} at {path}"
                errors.append(
                    SchemaValidationError(
                        path=path,
                        message=msg,
                        validator="type",
                    )
                )
                return

        if isinstance(instance, dict):
            # Check required properties
            required_props = subschema.get("required", [])
            for prop in required_props:
                if prop not in instance:
                    sub_path = f"{path}.{prop}" if path != "$" else f"$.{prop}"
                    errors.append(
                        SchemaValidationError(
                            path=sub_path,
                            message=f"Missing required property '{prop}' at {path}",
                            validator="required",
                        )
                    )

            # Check properties
            properties = subschema.get("properties", {})
            for key, val in instance.items():
                if key in properties:
                    child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                    self._validate_node(properties[key], val, path=child_path, errors=errors)

        elif isinstance(instance, list):
            items_schema = subschema.get("items")
            if isinstance(items_schema, dict):
                for idx, item in enumerate(instance):
                    child_path = f"{path}[{idx}]"
                    self._validate_node(items_schema, item, path=child_path, errors=errors)

        elif isinstance(instance, str):
            pattern = subschema.get("pattern")
            if pattern:
                try:
                    if not re.search(pattern, instance):
                        errors.append(
                            SchemaValidationError(
                                path=path,
                                message=f"String does not match pattern '{pattern}' at {path}",
                                validator="pattern",
                            )
                        )
                except re.error:
                    pass


__all__ = ("JsonSchemaParserAdapter",)
