"""Identifier and module filename sanitization utilities."""

from __future__ import annotations

import keyword
import re
from pathlib import Path


def sanitize_identifier(name: str) -> str:
    """Sanitizes an arbitrary schema property name into a valid Python identifier.

    Rules:
    1. Strip leading '$' or common symbols used in JSON Schema ($schemaRef, $id).
    2. Convert remaining non-alphanumeric characters to underscores.
    3. Collapse multiple underscores and strip leading/trailing underscores.
    4. Default to 'field' if empty.
    5. Prefix with 'field_' if the identifier begins with a digit.
    6. Suffix with '_' if the identifier matches a Python keyword (e.g. 'from', 'class').
    """
    clean = name.lstrip("$")
    clean = re.sub(r"[^0-9a-zA-Z_]+", "_", clean).strip("_")

    if not clean:
        clean = "field"

    if clean[0].isdigit():
        clean = f"field_{clean}"

    if keyword.iskeyword(clean):
        clean = f"{clean}_"

    return clean


def normalize_module_filename(schema_path: str | Path) -> str:
    """Normalizes a schema path stem into a valid Python module filename.

    Example:
        'journal-v1.0.json' -> 'journal_v1_0.py'
    """
    path = Path(schema_path)
    name = path.name
    # Strip trailing .json if present
    if name.endswith(".json") and name != ".json":
        stem = name[:-5]
    elif name == ".json":
        stem = ""
    else:
        stem = path.stem

    clean_stem = re.sub(r"[^0-9a-zA-Z_]+", "_", stem).lower().strip("_")

    if not clean_stem:
        clean_stem = "schema_model"
    elif clean_stem[0].isdigit():
        clean_stem = f"model_{clean_stem}"

    return f"{clean_stem}.py"


def derive_class_title(schema_path: str | Path, explicit_title: str | None = None) -> str:
    """Derives a clean PascalCase class title from an explicit title or schema path."""
    if explicit_title and explicit_title.strip():
        # Retain internal casing if already alphanumeric
        clean_explicit = "".join(ch for ch in explicit_title.strip() if ch.isalnum() or ch == "_")
        if clean_explicit:
            # Ensure leading char is capitalized
            return clean_explicit[0].upper() + clean_explicit[1:]

    raw_name = Path(schema_path).name
    if raw_name.endswith(".json") and raw_name != ".json":
        raw = raw_name[:-5]
    elif raw_name == ".json":
        raw = ""
    else:
        raw = Path(schema_path).stem

    parts = re.split(r"[^0-9a-zA-Z]+", raw)
    title = "".join(part.capitalize() for part in parts if part)
    return title or "Model"


__all__ = (
    "derive_class_title",
    "normalize_module_filename",
    "sanitize_identifier",
)
