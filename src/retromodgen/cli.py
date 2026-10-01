from __future__ import annotations

import json
from pathlib import Path

import typer
from pydantic import ValidationError

from retromodgen.models.spec import AssetSpec
from retromodgen.profiles.loader import default_profile_dir, load_profile
from retromodgen.validation.profile import validate_spec_against_profile

app = typer.Typer(no_args_is_help=True)


@app.command("validate")
def validate_command(spec_file: Path) -> None:
    """Validate an AssetSpec and its target profile."""
    try:
        spec = AssetSpec.model_validate_json(spec_file.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        typer.echo(f"AssetSpec invalid: {exc}")
        raise typer.Exit(code=2)

    profile = load_profile(spec.profile)
    report = validate_spec_against_profile(spec, profile)

    typer.echo(json.dumps({
        "asset": spec.name,
        "profile": spec.profile,
        "ok": report.ok,
        "issues": [issue.__dict__ for issue in report.issues],
    }, indent=2))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command("profiles")
def profiles_command() -> None:
    """List locally available target profiles."""
    for path in sorted(default_profile_dir().glob("*.json")):
        typer.echo(path.stem)


if __name__ == "__main__":
    app()
