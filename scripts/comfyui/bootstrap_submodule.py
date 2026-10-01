from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args))
    return subprocess.run(args, cwd=cwd, text=True, check=check)


def capture(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/update the ComfyUI Git submodule.")
    parser.add_argument(
        "--init-repo",
        action="store_true",
        help="Run `git init` when this scaffold has not been initialized as a repository yet.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    lock = json.loads((root / "config/comfyui.lock.json").read_text(encoding="utf-8"))
    path = root / "third_party/ComfyUI"
    rel_path = "third_party/ComfyUI"

    try:
        capture("git", "rev-parse", "--is-inside-work-tree", cwd=root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        if not args.init_repo:
            raise SystemExit(
                "This scaffold is not a Git working tree. Run `git init` first, or rerun "
                "with --init-repo. Commit/stage the scaffold before publishing it."
            )
        run("git", "init", cwd=root)

    staged = ""
    try:
        staged = capture("git", "ls-files", "--stage", rel_path, cwd=root)
    except subprocess.CalledProcessError:
        pass

    if staged.startswith("160000 "):
        run("git", "submodule", "update", "--init", "--recursive", rel_path, cwd=root)
    else:
        if path.exists() and any(path.iterdir()):
            is_repo = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--git-dir"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0
            if not is_repo:
                raise SystemExit(f"{path} exists and is not a Git repository; move/remove it first.")
            run("git", "add", ".gitmodules", rel_path, cwd=root)
            run("git", "submodule", "absorbgitdirs", rel_path, cwd=root, check=False)
        else:
            run(
                "git",
                "submodule",
                "add",
                "--force",
                "-b",
                lock["branch"],
                lock["repository"],
                rel_path,
                cwd=root,
            )

    run("git", "-C", str(path), "fetch", "origin", lock["baseline_commit"], cwd=root)
    run("git", "-C", str(path), "checkout", "--detach", lock["baseline_commit"], cwd=root)
    run("git", "add", ".gitmodules", rel_path, cwd=root)

    actual = capture("git", "-C", str(path), "rev-parse", "HEAD", cwd=root)
    print(f"ComfyUI submodule pinned at {actual}")
    print("Next: commit .gitmodules and the third_party/ComfyUI gitlink in the parent repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
