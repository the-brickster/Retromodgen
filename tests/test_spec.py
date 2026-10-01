from retromodgen.models.spec import AssetSpec


def test_asset_spec_loads() -> None:
    spec = AssetSpec.model_validate({
        "name": "crate",
        "profile": "quake2_prop",
        "asset_type": "prop",
        "description": "industrial crate",
        "geometry": {"target_triangles": 200, "hard_max_triangles": 400},
        "texture": {"width": 128, "height": 128}
    })
    assert spec.geometry.target_triangles == 200
    assert spec.texture.filter == "nearest"
