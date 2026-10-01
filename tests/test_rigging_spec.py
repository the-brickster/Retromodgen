from __future__ import annotations

from pathlib import Path

from retromodgen.models.spec import AssetSpec


def test_example_character_uses_skeletal_rigging() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = AssetSpec.model_validate_json(
        (root / "examples/quake2_guard.asset.json").read_text(encoding="utf-8")
    )
    assert spec.rigging.mode == "skeletal"
    assert spec.rigging.generate_ik_controls is True
    assert spec.rigging.topology_freeze_required is True
    assert spec.animation.type == "skeletal"
    assert "glb" in spec.export.formats
    assert "md2" in spec.export.formats
