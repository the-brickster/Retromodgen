from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from retromodgen.models.spec import AssetSpec


@dataclass(frozen=True)
class CompileResult:
    mesh_path: Path
    texture_paths: tuple[Path, ...]
    stats: dict[str, int | float | str]


class MeshCompiler(ABC):
    @abstractmethod
    def compile(self, mesh_path: Path, spec: AssetSpec, work_dir: Path) -> CompileResult:
        raise NotImplementedError


class TextureCompiler(ABC):
    @abstractmethod
    def compile(
        self,
        source_mesh: Path,
        target_mesh: Path,
        spec: AssetSpec,
        work_dir: Path,
    ) -> tuple[Path, ...]:
        raise NotImplementedError
