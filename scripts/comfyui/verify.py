from __future__ import annotations

import argparse
import json

import httpx

REQUIRED_NODES = {
    "RetroModGen_LoadAssetSpec",
    "RetroModGen_LoadProfile",
    "RetroModGen_ValidateAssetSpec",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a running ComfyUI RetroModGen integration.")
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    with httpx.Client(timeout=10.0) as client:
        stats = client.get(f"{base}/system_stats")
        stats.raise_for_status()
        object_info = client.get(f"{base}/object_info")
        object_info.raise_for_status()

    nodes = set(object_info.json())
    missing = sorted(REQUIRED_NODES - nodes)
    result = {
        "server_ok": True,
        "required_nodes": sorted(REQUIRED_NODES),
        "missing_nodes": missing,
        "ok": not missing,
    }
    print(json.dumps(result, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
