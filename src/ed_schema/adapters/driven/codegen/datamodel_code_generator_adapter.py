"""Datamodel code generator adapter implementing DatamodelGeneratorPort."""

from __future__ import annotations

import json
import os
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

        Args:
            schema_path: Path to source JSON schema document.
            output_file: Path to destination Python file.
            class_prefix: PascalCase provider prefix (e.g., 'Capi', 'Inara').

        Raises:
            SchemaCompilationError: If generation fails due to syntax or file errors.
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

        # Build clean PascalCase class name
        title = derive_class_title(schema_path, schema_data.get("title"))
        clean_prefix = "".join(ch for ch in class_prefix if ch.isalnum() or ch == "_")
        class_name = f"{clean_prefix}{title}DTO"

        # Synthesize typed Python dataclass source code
        code_lines = [
            '"""Auto-generated Python dataclasses synthesized by ed-schema."""',
            "",
            "from __future__ import annotations",
            "",
            "from dataclasses import dataclass",
            "from typing import Any",
            "",
            "",
            "@dataclass(frozen=True)",
            f"class {class_name}:",
        ]

        docstring = schema_data.get("description", f"Data transfer object for {title}.")
        code_lines.append(f'    """{docstring}"""')
        code_lines.append("")

        properties: dict[str, Any] = schema_data.get("properties", {})
        required_fields: list[str] = schema_data.get("required", [])

        if not properties:
            code_lines.append("    pass")
            code_lines.append("")
        else:
            # Required fields first, then optional fields with defaults
            req_props = [p for p in properties if p in required_fields]
            opt_props = [p for p in properties if p not in required_fields]

            type_map = {
                "string": "str",
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "object": "dict[str, Any]",
                "array": "list[Any]",
            }

            for p in req_props:
                p_schema = properties[p]
                t_str = type_map.get(p_schema.get("type", ""), "Any")
                clean_field = sanitize_identifier(p)
                code_lines.append(f"    {clean_field}: {t_str}")

            for p in opt_props:
                p_schema = properties[p]
                t_str = type_map.get(p_schema.get("type", ""), "Any")
                clean_field = sanitize_identifier(p)
                code_lines.append(f"    {clean_field}: {t_str} | None = None")

            code_lines.append("")

        code_lines.append(f'__all__ = ("{class_name}",)')
        code_lines.append("")

        generated_code = "\n".join(code_lines)

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            # Write atomically using temporary file in same directory
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_file.parent,
                delete=False,
            ) as tmp_file:
                tmp_file.write(generated_code)
                tmp_path = Path(tmp_file.name)

            os.replace(tmp_path, output_file)
        except OSError as exc:
            msg = f"Failed writing generated dataclass to '{output_file}': {exc}"
            raise SchemaCompilationError(msg) from exc


__all__ = ("DatamodelCodeGeneratorAdapter",)
