from __future__ import annotations

from pathlib import Path

import httpx

from retromodgen.backends.base import GeneratedAsset, GeometryBackend
from retromodgen.models.spec import AssetSpec


class ComfyUIBackend(GeometryBackend):
    """Adapter boundary for a ComfyUI workflow.

    Phase 1 intentionally does not hard-code one workflow JSON. The workflow becomes
    a versioned backend configuration later so Hunyuan/TRELLIS nodes can be swapped.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8188") -> None:
        self.base_url = base_url.rstrip("/")

    def healthcheck(self) -> None:
        response = httpx.get(f"{self.base_url}/system_stats", timeout=5.0)
        response.raise_for_status()

    def generate(self, spec: AssetSpec, work_dir: Path) -> GeneratedAsset:
        raise NotImplementedError(
            "ComfyUI workflow submission is a Phase 1 implementation task. "
            "Keep workflow JSON outside this adapter and inject it as configuration."
        )
