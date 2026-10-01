"""Tracked ComfyUI loader for RetroModGen custom nodes.

Launch the ComfyUI submodule with --base-directory <repo>/.comfy. The Comfy Python
environment must have this repository installed editable (`pip install -e <repo>`).
"""

from retromodgen_comfy import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
