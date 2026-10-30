"""End-to-end integration test exercising SchemaEngine."""

from __future__ import annotations

import json
from pathlib import Path

from ed_schema import (
    EndpointContract,
    HeaderContract,
    HeaderParameterContract,
    SchemaKey,
    create_schema_engine,
)


def test_schema_engine_e2e_workflow(tmp_path: Path) -> None:
    """Verifies end-to-end manifest loading, validation, compilation, and parity."""
    # 1. Setup sample schema directory
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    models_dir = tmp_path / "models"

    profile_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "CommanderProfile",
        "description": "Commander profile response payload.",
        "type": "object",
        "required": ["commander_id", "name"],
        "properties": {
            "commander_id": {"type": "string"},
            "name": {"type": "string"},
            "credits": {"type": "integer"},
        },
    }
    schema_file = schemas_dir / "profile.json"
    schema_file.write_text(json.dumps(profile_schema), encoding="utf-8")

    # 2. Instantiate production SchemaEngine
    engine = create_schema_engine()

    # 3. Define manifest stub and batch load
    class CapiManifest:
        name = "capi"
        schema_dir = schemas_dir
        endpoints = (
            EndpointContract(
                route="/profile",
                schema_file="profile.json",
                header_contract=HeaderContract(
                    parameters=(
                        HeaderParameterContract(
                            name="Authorization",
                            required=True,
                            regex_pattern=r"^Bearer\s+[A-Za-z0-9]+$",
                        ),
                    )
                ),
            ),
        )

    loaded_count = engine.load_manifests([CapiManifest()])
    assert loaded_count == 1

    # 4. Resolve descriptor
    key = SchemaKey(namespace="capi", endpoint="/profile")
    descriptor = engine.resolve_descriptor(key)
    assert descriptor is not None
    assert descriptor.schema_definition["title"] == "CommanderProfile"

    # 5. Pre-flight validate call: successful case
    good_validation = engine.validate_call(
        key=key,
        headers={"Authorization": "Bearer secret123"},
        payload={"commander_id": "c1", "name": "Jameson"},
    )
    assert good_validation.is_valid is True
    assert not good_validation.has_errors

    # 6. Pre-flight validate call: invalid header case
    bad_validation = engine.validate_call(
        key=key,
        headers={"Authorization": "Basic invalid"},
        payload={"commander_id": "c1", "name": "Jameson"},
    )
    assert bad_validation.is_valid is False
    assert len(bad_validation.header_errors) > 0

    # 7. Compile dataclasses to disk
    compiled = engine.compile_models(
        schema_dir=schemas_dir,
        output_dir=models_dir,
        class_prefix="Capi",
    )
    assert len(compiled) == 1
    assert compiled[0].exists()

    # 8. Verify parity between schema and generated model
    parity = engine.verify_parity(
        schema_dir=schemas_dir,
        models_dir=models_dir,
        namespace="capi",
        class_prefix="Capi",
    )
    assert parity.is_synchronized is True
    assert len(parity.mismatches) == 0
