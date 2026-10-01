from __future__ import annotations

import json
from pathlib import Path

from retromodgen.models.spec import AssetSpec
from retromodgen.profiles.loader import load_profile
from retromodgen.validation.profile import validate_spec_against_profile

ASSET_SPEC_TYPE = "RETROMODGEN_ASSET_SPEC"
PROFILE_TYPE = "RETROMODGEN_PROFILE"


class RetroLoadAssetSpecNode:
    """Load a serialized AssetSpec without requiring ComfyUI imports."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset_spec_path": (
                    "STRING",
                    {"default": "examples/quake2_guard.asset.json", "multiline": False},
                )
            }
        }

    RETURN_TYPES = (ASSET_SPEC_TYPE, "STRING")
    RETURN_NAMES = ("asset_spec", "asset_spec_json")
    FUNCTION = "load"
    CATEGORY = "RetroModGen/Spec"

    def load(self, asset_spec_path: str):
        path = Path(asset_spec_path).expanduser().resolve()
        spec = AssetSpec.model_validate_json(path.read_text(encoding="utf-8"))
        return (spec, spec.model_dump_json(indent=2))


class RetroLoadProfileNode:
    """Load a named RetroModGen target profile."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "profile_name": (
                    "STRING",
                    {"default": "quake2_character", "multiline": False},
                )
            }
        }

    RETURN_TYPES = (PROFILE_TYPE, "STRING")
    RETURN_NAMES = ("profile", "profile_json")
    FUNCTION = "load"
    CATEGORY = "RetroModGen/Spec"

    def load(self, profile_name: str):
        profile = load_profile(profile_name)
        return (profile, json.dumps(profile, indent=2, sort_keys=True))


class RetroValidateAssetSpecNode:
    """Validate an AssetSpec against a loaded or implied profile."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset_spec": (ASSET_SPEC_TYPE,),
            },
            "optional": {
                "profile": (PROFILE_TYPE,),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("valid", "report_json")
    FUNCTION = "validate"
    CATEGORY = "RetroModGen/Validation"

    def validate(self, asset_spec: AssetSpec, profile: dict | None = None):
        resolved_profile = profile or load_profile(asset_spec.profile)
        report = validate_spec_against_profile(asset_spec, resolved_profile)
        payload = {
            "ok": report.ok,
            "issues": [
                {
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in report.issues
            ],
        }
        return (report.ok, json.dumps(payload, indent=2, sort_keys=True))
