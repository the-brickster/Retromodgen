from __future__ import annotations

import configparser
import json
from pathlib import Path


def test_comfy_submodule_and_lock_agree() -> None:
    root = Path(__file__).resolve().parents[2]
    lock = json.loads((root / "config/comfyui.lock.json").read_text(encoding="utf-8"))

    parser = configparser.ConfigParser()
    parser.read(root / ".gitmodules")
    section = parser['submodule "third_party/ComfyUI"']

    assert section["path"] == "third_party/ComfyUI"
    assert section["url"] == lock["repository"]
    assert section["branch"] == lock["branch"]
    assert len(lock["baseline_commit"]) == 40
    int(lock["baseline_commit"], 16)
