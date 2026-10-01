from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the pinned ComfyUI submodule for RetroModGen.")
    parser.add_argument("--python", default=os.environ.get("RETROMODGEN_COMFY_PYTHON", sys.executable))
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", default="8188")
    args, passthrough = parser.parse_known_args()

    root = Path(__file__).resolve().parents[2]
    comfy = root / "third_party/ComfyUI/main.py"
    base = root / ".comfy"
    if not comfy.exists():
        raise SystemExit(
            "ComfyUI submodule is not initialized. Run scripts/comfyui/bootstrap_submodule.py first."
        )

    cmd = [
        args.python,
        str(comfy),
        "--base-directory",
        str(base),
        "--listen",
        args.listen,
        "--port",
        str(args.port),
        *passthrough,
    ]
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
