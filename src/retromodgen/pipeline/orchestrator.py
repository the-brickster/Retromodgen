from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from retromodgen.backends.base import GeometryBackend
from retromodgen.models.spec import AssetSpec


class Stage(str, Enum):
    SPEC = "spec"
    SOURCE_GENERATION = "source_generation"
    GEOMETRY_COMPILE = "geometry_compile"
    TEXTURE_COMPILE = "texture_compile"
    ANIMATION_COMPILE = "animation_compile"
    VALIDATE = "validate"
    EXPORT = "export"
    PREVIEW = "preview"


@dataclass
class PipelineContext:
    spec: AssetSpec
    work_dir: Path


class Pipeline:
    """Explicit staged pipeline; no implicit magic between stages."""

    def __init__(self, backend: GeometryBackend) -> None:
        self.backend = backend

    def generate_source(self, ctx: PipelineContext):
        ctx.work_dir.mkdir(parents=True, exist_ok=True)
        return self.backend.generate(ctx.spec, ctx.work_dir)
