"""Datamodel code generator adapter implementing DatamodelGeneratorPort."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ed_schema.core.domain.exceptions import SchemaCompilationError
from ed_schema.core.domain.sanitization import (
    derive_class_title,
    sanitize_identifier,
)
from ed_schema.core.ports.driven.datamodel_generator_port import (
    DatamodelGeneratorPort,
)


class DatamodelCodeGeneratorAdapter(DatamodelGeneratorPort):
    """Secondary SPI adapter compiling JSON schemas to typed frozen Python dataclasses."""

    def generate_dataclasses(
        self,
        schema_path: Path,
        output_file: Path,
        class_prefix: str,
    ) -> None:
        """Generates a typed Python dataclass file from a JSON schema.

        Recursively synthesizes nested dataclasses for child object properties and object arrays.
        """
        if not schema_path.exists():
            msg = f"Schema file not found for compilation: {schema_path}"
            raise SchemaCompilationError(msg)

        try:
            raw_text = schema_path.read_text(encoding="utf-8")
            schema_data = json.loads(raw_text)
        except Exception as exc:
            msg = f"Failed reading schema document '{schema_path}': {exc}"
            raise SchemaCompilationError(msg) from exc

        if not isinstance(schema_data, dict):
            msg = f"Schema root must be an object: {schema_path}"
            raise SchemaCompilationError(msg)

        clean_prefix = "".join(ch for ch in class_prefix if ch.isalnum() or ch == "_")
        root_title = derive_class_title(schema_path, schema_data.get("title"))
        root_class_name = f"{clean_prefix}{root_title}DTO"

        # Collect all classes (child classes first, root class last)
        classes_code: list[str] = []
        exported_classes: list[str] = []

        def _resolve_type(
            prop_name: str,
            prop_schema: dict[str, Any],
            parent_class: str,
        ) -> str:
            """Resolves the Python type string for a schema property, recursing if object."""
            p_type = prop_schema.get("type")

            if p_type == "string":
                return "str"
            if p_type == "integer":
                return "int"
            if p_type == "number":
                return "float"
            if p_type == "boolean":
                return "bool"

            if p_type == "object":
                child_props = prop_schema.get("properties")
                if isinstance(child_props, dict) and child_props:
                    child_title = "".join(
                        part.capitalize() for part in re.split(r"[^0-9a-zA-Z]+", prop_name) if part
                    )
                    base_parent = (
                        parent_class[:-3] if parent_class.endswith("DTO") else parent_class
                    )
                    child_class = f"{base_parent}{child_title}DTO"
                    _generate_single_class(child_class, prop_schema)
                    return child_class
                return "dict[str, Any]"

            if p_type == "array":
                items = prop_schema.get("items")
                if isinstance(items, dict):
                    item_type = items.get("type")
                    if item_type == "object" and isinstance(items.get("properties"), dict):
                        item_title = "".join(
                            part.capitalize()
                            for part in re.split(r"[^0-9a-zA-Z]+", prop_name)
                            if part
                        )
                        base_parent = (
                            parent_class[:-3] if parent_class.endswith("DTO") else parent_class
                        )
                        child_class = f"{base_parent}{item_title}ItemDTO"
                        _generate_single_class(child_class, items)
                        return f"list[{child_class}]"
                    item_sub_type = _resolve_type(f"{prop_name}_item", items, parent_class)
                    return f"list[{item_sub_type}]"
                return "list[Any]"

            return "Any"

        def _generate_single_class(class_name: str, schema_dict: dict[str, Any]) -> None:
            """Synthesizes code for a single dataclass and adds it to classes_code."""
            lines: list[str] = [
                "@dataclass(frozen=True)",
                f"class {class_name}:",
            ]
            doc = schema_dict.get("description", f"Data transfer object for {class_name}.")
            lines.append(f'    """{doc}"""')
            lines.append("")

            properties: dict[str, Any] = schema_dict.get("properties", {})
            required_fields: list[str] = schema_dict.get("required", [])

            if not properties:
                lines.append("    pass")
            else:
                req_props = [p for p in properties if p in required_fields]
                opt_props = [p for p in properties if p not in required_fields]

                for p in req_props:
                    p_schema = properties[p] if isinstance(properties[p], dict) else {}
                    t_str = _resolve_type(p, p_schema, class_name)
                    clean_field = sanitize_identifier(p)
                    lines.append(f"    {clean_field}: {t_str}")

                for p in opt_props:
                    p_schema = properties[p] if isinstance(properties[p], dict) else {}
                    t_str = _resolve_type(p, p_schema, class_name)
                    clean_field = sanitize_identifier(p)
                    lines.append(f"    {clean_field}: {t_str} | None = None")

            lines.append("")
            classes_code.append("\n".join(lines))
            exported_classes.append(class_name)

        # Generate root and all nested classes
        _generate_single_class(root_class_name, schema_data)

        # Build complete source document
        header_lines = [
            '"""Auto-generated Python dataclasses synthesized by ed-schema."""',
            "",
            "from __future__ import annotations",
            "",
            "from dataclasses import dataclass",
            "from typing import Any",
            "",
            "",
        ]

        # In topological order: nested child classes first, then parent/root class
        # _generate_single_class adds children recursively during field evaluation.
        # Since _resolve_type called _generate_single_class before parent class
        # definition completed, classes_code already has children before parent.
        full_code = (
            "\n".join(header_lines)
            + "\n\n".join(classes_code)
            + f"\n__all__ = {tuple(exported_classes)!r}\n"
        )

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_file.parent,
                delete=False,
            ) as tmp_file:
                tmp_file.write(full_code)
                tmp_path = Path(tmp_file.name)

            os.replace(tmp_path, output_file)
        except OSError as exc:
            msg = f"Failed writing generated dataclass to '{output_file}': {exc}"
            raise SchemaCompilationError(msg) from exc


__all__ = ("DatamodelCodeGeneratorAdapter",)
