from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from retromodgen.models.spec import AssetSpec


class Exporter(ABC):
    @abstractmethod
    def export(self, compiled_mesh: Path, spec: AssetSpec, output_path: Path) -> Path:
        raise NotImplementedError
