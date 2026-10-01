"""ComfyUI custom-node surface for RetroModGen.

This package deliberately imports only RetroModGen core modules. ComfyUI discovers the
mappings through the thin loader in .comfy/custom_nodes/retromodgen_comfy.
"""

from retromodgen_comfy.nodes.spec_nodes import (
    RetroLoadAssetSpecNode,
    RetroLoadProfileNode,
    RetroValidateAssetSpecNode,
)

NODE_CLASS_MAPPINGS = {
    "RetroModGen_LoadAssetSpec": RetroLoadAssetSpecNode,
    "RetroModGen_LoadProfile": RetroLoadProfileNode,
    "RetroModGen_ValidateAssetSpec": RetroValidateAssetSpecNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RetroModGen_LoadAssetSpec": "RetroModGen • Load AssetSpec",
    "RetroModGen_LoadProfile": "RetroModGen • Load Profile",
    "RetroModGen_ValidateAssetSpec": "RetroModGen • Validate AssetSpec",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
