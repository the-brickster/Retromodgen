# Generation Backends

## Design rule

No model is the product. A backend is a replaceable source of geometry/material information.

## Interface

```python
class GeometryBackend(ABC):
    def generate(self, spec: AssetSpec, work_dir: Path) -> GeneratedAsset:
        ...
```

`GeneratedAsset` is intentionally simple: mesh path, texture paths, metadata.

## ComfyUI integration

ComfyUI is both an optional inference scheduler **and** a first-class node-graph authoring surface. RetroModGen supports two complementary integration modes:

1. `retromodgen -> ComfyUI` through HTTP/WebSocket workflow submission for CLI/headless generation.
2. `ComfyUI -> retromodgen` through custom nodes that call the same core compiler/rigging/export APIs.

The ComfyUI source checkout is kept as an optional Git submodule at `third_party/ComfyUI`, while runtime data lives under `.comfy/` via ComfyUI's `--base-directory` option. See `docs/COMFYUI_INTEGRATION.md`.

Custom nodes are thin adapters. They may expose editor controls and call core functions, but they must not duplicate profile rules, mesh simplification, texture compilation, rigging, validation, or exporters.

Good inference responsibilities inside ComfyUI include:

- background removal;
- concept/reference generation;
- multiview generation;
- Hunyuan/TRELLIS inference;
- model loading/offloading;
- GPU queueing.

RetroModGen core remains the owner of:

- canonical `AssetSpec` and target profiles;
- QEM/retro simplification;
- UV/texture compilation;
- topology freeze and skeletal rig data;
- skin/IK/animation compilation;
- classic format validation;
- GLB/MDL/MD2 exporters;
- asset cache/provenance.

## Workflow registry

Eventually:

```text
workflows/comfyui/
  spec_validate.api.json
  hunyuan_source_mesh.api.json
  trellis_source_mesh.api.json
  retro_static_prop.api.json
  retro_character_rigged_glb.api.json
```

Each workflow gets metadata:

```json
{
  "backend": "hunyuan2",
  "workflow_version": "1.2.0",
  "required_inputs": ["front_image"],
  "produces": ["mesh", "source_texture"]
}
```

## Direct backends

A direct Python/service backend can bypass ComfyUI. The remainder of the system should not notice.

This is important for automated testing and future headless build-farm execution.
