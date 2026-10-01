from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProfileNotFoundError(FileNotFoundError):
    pass


def default_profile_dir() -> Path:
    # src/retromodgen/profiles/loader.py -> repository root during editable installs.
    return Path(__file__).resolve().parents[3] / "profiles"


def load_profile(name: str, profile_dir: Path | None = None) -> dict[str, Any]:
    root = profile_dir or default_profile_dir()
    path = root / f"{name}.json"
    if not path.exists():
        raise ProfileNotFoundError(f"Profile not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
