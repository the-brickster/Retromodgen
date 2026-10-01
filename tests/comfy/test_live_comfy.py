from __future__ import annotations

import os

import httpx
import pytest


@pytest.mark.comfy_live
def test_live_comfy_discovers_retromodgen_nodes() -> None:
    if os.environ.get("RETROMODGEN_COMFY_LIVE") != "1":
        pytest.skip("set RETROMODGEN_COMFY_LIVE=1 to run live ComfyUI smoke tests")

    base = os.environ.get("RETROMODGEN_COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
    info = httpx.get(f"{base}/object_info", timeout=10).json()
    for name in (
        "RetroModGen_LoadAssetSpec",
        "RetroModGen_LoadProfile",
        "RetroModGen_ValidateAssetSpec",
    ):
        assert name in info
