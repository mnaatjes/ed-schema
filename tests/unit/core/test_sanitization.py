"""Unit tests for domain sanitization utilities."""

from __future__ import annotations

from pathlib import Path

from ed_schema.core.domain.sanitization import (
    derive_class_title,
    normalize_module_filename,
    sanitize_identifier,
)


def test_sanitize_identifier_dollar_sign() -> None:
    assert sanitize_identifier("$schemaRef") == "schemaRef"
    assert sanitize_identifier("$id") == "id"
    assert sanitize_identifier("$$raw") == "raw"


def test_sanitize_identifier_illegal_characters() -> None:
    assert sanitize_identifier("kebab-case-field") == "kebab_case_field"
    assert sanitize_identifier("spaced field name") == "spaced_field_name"
    assert sanitize_identifier("dot.separated.name") == "dot_separated_name"
    assert sanitize_identifier("mixed/slash+plus") == "mixed_slash_plus"


def test_sanitize_identifier_keywords() -> None:
    assert sanitize_identifier("import") == "import_"
    assert sanitize_identifier("from") == "from_"
    assert sanitize_identifier("class") == "class_"
    assert sanitize_identifier("def") == "def_"


def test_sanitize_identifier_leading_digit() -> None:
    assert sanitize_identifier("123item") == "field_123item"
    assert sanitize_identifier("42") == "field_42"


def test_sanitize_identifier_empty_fallback() -> None:
    assert sanitize_identifier("") == "field"
    assert sanitize_identifier("$$$") == "field"
    assert sanitize_identifier("---") == "field"


def test_normalize_module_filename() -> None:
    assert normalize_module_filename("journal-v1.0.json") == "journal_v1_0.py"
    assert (
        normalize_module_filename(Path("schemas/eddn/commodity-v3.0.json")) == "commodity_v3_0.py"
    )
    assert normalize_module_filename("simple.json") == "simple.py"
    assert normalize_module_filename("123start.json") == "model_123start.py"
    assert normalize_module_filename(".json") == "schema_model.py"


def test_derive_class_title() -> None:
    assert derive_class_title("journal-v1.0.json") == "JournalV10"
    assert (
        derive_class_title(
            "profile.json",
            explicit_title="CommanderProfile",
        )
        == "CommanderProfile"
    )
    assert derive_class_title("simple_event.json") == "SimpleEvent"
    assert derive_class_title(".json") == "Model"
