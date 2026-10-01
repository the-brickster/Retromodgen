from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from retromodgen.models.spec import AssetSpec


@dataclass(frozen=True)
class GeneratedAsset:
    mesh_path: Path
    texture_paths: tuple[Path, ...] = ()
    metadata: dict[str, object] | None = None


class GeometryBackend(ABC):
    """Stable boundary between retromodgen and any 3D foundation model."""

    @abstractmethod
    def generate(self, spec: AssetSpec, work_dir: Path) -> GeneratedAsset:
        raise NotImplementedError
