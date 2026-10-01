from __future__ import annotations

import json
from pathlib import Path

from retromodgen_comfy import NODE_CLASS_MAPPINGS
from retromodgen_comfy.nodes.spec_nodes import (
    RetroLoadAssetSpecNode,
    RetroLoadProfileNode,
    RetroValidateAssetSpecNode,
)


def test_initial_node_mappings_are_exposed() -> None:
    assert {
        "RetroModGen_LoadAssetSpec",
        "RetroModGen_LoadProfile",
        "RetroModGen_ValidateAssetSpec",
    }.issubset(NODE_CLASS_MAPPINGS)


def test_spec_profile_validation_nodes_work_without_comfyui() -> None:
    root = Path(__file__).resolve().parents[2]
    spec, _ = RetroLoadAssetSpecNode().load(str(root / "examples/quake2_guard.asset.json"))
    profile, _ = RetroLoadProfileNode().load("quake2_character")
    ok, report_json = RetroValidateAssetSpecNode().validate(spec, profile)
    report = json.loads(report_json)
    assert ok is True
    assert report["ok"] is True
    assert report["issues"] == []


def test_comfy_api_workflow_references_registered_nodes() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = json.loads((root / "workflows/comfyui/spec_validate.api.json").read_text())
    registered = set(NODE_CLASS_MAPPINGS)
    for node in workflow.values():
        assert node["class_type"] in registered
