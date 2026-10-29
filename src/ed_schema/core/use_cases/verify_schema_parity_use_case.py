"""Use case for verifying structural parity between schemas and DTOs (UC-03)."""

from __future__ import annotations

import ast
from pathlib import Path

from ed_schema.core.domain.exceptions import SchemaParityError
from ed_schema.core.domain.models import ParityMismatch, ParityReport
from ed_schema.core.ports.driven.schema_storage_port import SchemaStoragePort


class VerifySchemaParityUseCase:
    """Orchestrates in-process AST parity verification between schemas and models."""

    def __init__(self, storage: SchemaStoragePort) -> None:
        self._storage = storage

    def execute(
        self,
        schema_dir: Path,
        models_dir: Path,
        namespace: str,
        class_prefix: str,
    ) -> ParityReport:
        """Performs AST parity inspection and produces ParityReport."""
        if not namespace or not namespace.strip():
            raise SchemaParityError("namespace must be a non-empty string.")

        try:
            schema_files = self._storage.list_schema_files(schema_dir)
        except Exception as exc:
            raise SchemaParityError(
                f"Failed listing schema files in '{schema_dir}': {exc}"
            ) from exc

        mismatches: list[ParityMismatch] = []

        for schema_file in schema_files:
            if not schema_file.name.endswith(".json"):
                continue

            try:
                schema_doc = self._storage.read_schema_document(schema_file)
            except Exception as exc:
                raise SchemaParityError(
                    f"Failed reading schema document '{schema_file}': {exc}"
                ) from exc

            properties = schema_doc.get("properties", {})
            required_fields = set(schema_doc.get("required", []))

            stem = schema_file.stem
            model_file = models_dir / f"{stem}.py"

            if not model_file.exists():
                mismatches.append(
                    ParityMismatch(
                        entity_name=f"{class_prefix}{stem.capitalize()}DTO",
                        attribute_name="__file__",
                        mismatch_type="MISSING_FILE",
                        description=f"Generated model file does not exist: {model_file}",
                    )
                )
                continue

            try:
                tree = ast.parse(model_file.read_text(encoding="utf-8"), filename=str(model_file))
            except Exception as exc:
                raise SchemaParityError(
                    f"Syntax error parsing model file '{model_file}': {exc}"
                ) from exc

            model_fields: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            model_fields.add(item.target.id)

            for prop_name in properties:
                if prop_name in required_fields and prop_name not in model_fields:
                    mismatches.append(
                        ParityMismatch(
                            entity_name=f"{class_prefix}{stem.capitalize()}DTO",
                            attribute_name=prop_name,
                            mismatch_type="MISSING_FIELD",
                            description=(
                                f"Required schema property '{prop_name}' missing in "
                                f"{model_file.name}"
                            ),
                        )
                    )

        is_sync = len(mismatches) == 0
        return ParityReport(
            namespace=namespace,
            is_synchronized=is_sync,
            mismatches=tuple(mismatches),
        )


__all__ = ("VerifySchemaParityUseCase",)
