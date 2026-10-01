from retromodgen.models.spec import AssetSpec
from retromodgen.validation.profile import validate_spec_against_profile


def test_profile_rejects_triangle_limit() -> None:
    spec = AssetSpec.model_validate({
        "name": "too_big",
        "profile": "quake2_character",
        "asset_type": "character",
        "description": "test",
        "geometry": {"target_triangles": 3000, "hard_max_triangles": 5000},
        "texture": {"width": 128, "height": 128}
    })
    profile = {"hard_limits": {"max_triangles": 4096}}
    report = validate_spec_against_profile(spec, profile)
    assert not report.ok
