"""Unified programmatic driving facade for ed-schema."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ed_schema.core.domain.models import (
    ParityReport,
    SchemaDescriptor,
    SchemaKey,
    ValidationResult,
)
from ed_schema.core.use_cases.compile_dataclasses_use_case import (
    CompileDataclassesUseCase,
)
from ed_schema.core.use_cases.register_schema_use_case import (
    RegisterSchemaUseCase,
)
from ed_schema.core.use_cases.validate_pre_flight_contract_use_case import (
    ValidatePreFlightContractUseCase,
)
from ed_schema.core.use_cases.verify_schema_parity_use_case import (
    VerifySchemaParityUseCase,
)


class SchemaEngine:
    """Primary programmatic driving facade for ed-schema."""

    def __init__(
        self,
        register_use_case: RegisterSchemaUseCase,
        validate_use_case: ValidatePreFlightContractUseCase,
        compile_use_case: CompileDataclassesUseCase,
        parity_use_case: VerifySchemaParityUseCase,
    ) -> None:
        self._register_uc = register_use_case
        self._validate_uc = validate_use_case
        self._compile_uc = compile_use_case
        self._parity_uc = parity_use_case

    # -------------------------------------------------------------------------
    # 1. Registry & Manifest Ingestion (ADR 0001, UC-01)
    # -------------------------------------------------------------------------
    def register_descriptor(self, descriptor: SchemaDescriptor) -> None:
        """Stores a schema descriptor in the in-memory registry."""
        self._register_uc.register(descriptor)

    def resolve_descriptor(self, key: SchemaKey) -> SchemaDescriptor | None:
        """Resolves a registered schema descriptor in microseconds."""
        return self._register_uc.resolve(key)

    def load_manifests(self, manifests: Sequence[Any]) -> int:
        """Batch loads schemas across provider manifest declarations."""
        return self._register_uc.execute(manifests)

    # -------------------------------------------------------------------------
    # 2. Build-Time Code Generation (ADR 0002, ADR 0004, UC-02)
    # -------------------------------------------------------------------------
    def compile_models(
        self,
        schema_dir: str | Path,
        output_dir: str | Path,
        class_prefix: str,
    ) -> tuple[Path, ...]:
        """Compiles canonical JSON schemas into typed Python dataclasses."""
        return self._compile_uc.execute(
            schema_dir=Path(schema_dir),
            output_dir=Path(output_dir),
            class_prefix=class_prefix,
        )

    # -------------------------------------------------------------------------
    # 3. In-Process Parity Verification (ADR 0003, ADR 0007, UC-03)
    # -------------------------------------------------------------------------
    def verify_parity(
        self,
        schema_dir: str | Path,
        models_dir: str | Path,
        namespace: str,
        class_prefix: str,
    ) -> ParityReport:
        """Verifies structural AST equivalence between schemas and models."""
        return self._parity_uc.execute(
            schema_dir=Path(schema_dir),
            models_dir=Path(models_dir),
            namespace=namespace,
            class_prefix=class_prefix,
        )

    # -------------------------------------------------------------------------
    # 4. Composite Pre-Flight Validation (ADR 0005, UC-04)
    # -------------------------------------------------------------------------
    def validate_call(
        self,
        key: SchemaKey,
        headers: Mapping[str, str],
        payload: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Unified pre-flight validation gate verifying both headers and payload."""
        return self._validate_uc.execute(
            key=key,
            headers=headers,
            payload=payload,
        )


__all__ = ("SchemaEngine",)
