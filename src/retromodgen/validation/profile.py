from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from retromodgen.models.spec import AssetSpec


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def validate_spec_against_profile(spec: AssetSpec, profile: dict[str, Any]) -> ValidationReport:
    issues: list[ValidationIssue] = []
    hard = profile.get("hard_limits", {})

    max_triangles = hard.get("max_triangles")
    if max_triangles is not None and spec.geometry.hard_max_triangles > max_triangles:
        issues.append(
            ValidationIssue(
                "error",
                "triangle_limit",
                f"Spec hard_max_triangles={spec.geometry.hard_max_triangles} exceeds profile limit={max_triangles}",
            )
        )

    allowed_texture_sizes = profile.get("allowed_texture_sizes")
    size = [spec.texture.width, spec.texture.height]
    if allowed_texture_sizes and size not in allowed_texture_sizes:
        issues.append(
            ValidationIssue(
                "error",
                "texture_size",
                f"Texture size {size[0]}x{size[1]} is not allowed by profile {spec.profile}",
            )
        )

    if profile.get("requires_flat_shading") and not spec.geometry.flat_shading:
        issues.append(
            ValidationIssue(
                "warning",
                "flat_shading",
                "Profile expects flat/faceted shading but the AssetSpec disables it",
            )
        )

    return ValidationReport(tuple(issues))
