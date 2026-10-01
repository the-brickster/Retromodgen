from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install RetroModGen editable into the Python environment used to run ComfyUI."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used by ComfyUI. Set this explicitly when ComfyUI uses another venv.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    cmd = [args.python, "-m", "pip", "install", "-e", f"{root}[comfy]"]
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
