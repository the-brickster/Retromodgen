# retromodgen

`retromodgen` is a model-agnostic harness and deterministic retro-asset compiler for generating low-poly game assets, with first-class Quake 1 / Quake II-style profiles and bone-based skeletal rigging for articulated models.

The project deliberately separates **generation** from **retro compilation**:

1. A user, LLM, CLI, or ComfyUI graph produces a deterministic `AssetSpec`.
2. A replaceable generation backend creates source geometry/materials.
3. RetroModGen compiles geometry, UVs, textures, rigging, and animation toward a target profile.
4. Validators enforce profile and engine-format limits.
5. Exporters emit rigged GLB/GLTF and optional classic MDL/MD2 assets.

The goal is not merely “low poly.” Geometry, texture resolution/palette, shading, rigging, animation, and file-format constraints are deliberate parts of the asset specification.

## Core design principles

- **Profiles, not vague prompts.** Triangle budget, texture size, palette, shading, rigging, animation, and export limits are explicit data.
- **Model-agnostic.** Hunyuan, TRELLIS, or another generator can be swapped without changing the compiler.
- **Compiler-first.** Retro geometry/texture processing is deterministic and independently testable.
- **Bone rigs are canonical.** Characters/creatures/articulated assets keep skeletal rigs for editing, IK, retargeting, and modern runtime use; MDL/MD2 vertex frames are optional export bakes.
- **ComfyUI is first-class but optional.** It is both a node-graph authoring surface and an inference backend, not a hard core dependency.
- **Fail loudly.** Validators explain why an asset violates a profile or native-format constraint.
- **Keep it simple.** Python orchestrates; native C++ is reserved for proven performance-sensitive mesh operations.

## Architecture

```text
                           ComfyUI node editor
                                  |
                         retromodgen_comfy nodes
                                  |
                                  v
User / ChatGPT / CLI ------> AssetSpec / RetroModGen core
                                  |
             +--------------------+--------------------+
             |                                         |
             v                                         v
    source generation backend                 deterministic compiler
    ComfyUI / direct model                 geometry / texture / rigging
             |                                         |
             +--------------------+--------------------+
                                  v
                              validation
                                  |
                  +---------------+---------------+
                  |                               |
                  v                               v
             rigged GLB/GLTF                  MDL / MD2
```

ComfyUI can also be driven headlessly by the RetroModGen CLI through its HTTP/WebSocket API.

## Repository layout

```text
retromodgen/
├── .comfy/                         # RetroModGen-owned Comfy runtime base directory
│   └── custom_nodes/
│       └── retromodgen_comfy/      # tracked Comfy loader
├── config/
│   └── comfyui.lock.json           # integration baseline/pin
├── docs/
│   ├── ARCHITECTURE.md
│   ├── COMFYUI_INTEGRATION.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── ...
├── examples/
├── native/                         # future performance-sensitive C++
├── profiles/                       # versioned retro target profiles
├── scripts/comfyui/                # submodule/bootstrap/run/verify helpers
├── src/
│   ├── retromodgen/                # core library
│   └── retromodgen_comfy/          # Comfy custom-node package
├── third_party/
│   └── ComfyUI/                    # Git submodule after bootstrap
├── workflows/comfyui/              # versioned workflow templates
└── tests/
```

## Core-only development

ComfyUI is **not required** for most development.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
# source .venv/bin/activate

pip install -e ".[dev,mesh]"
pytest
retromodgen validate examples/quake2_guard.asset.json
```

## Optional ComfyUI submodule

The scaffold includes `.gitmodules` and a baseline commit record, but a ZIP does not itself contain a Git submodule gitlink. When starting from the scaffold ZIP:

```bash
git init
git add .
git commit -m "Initial RetroModGen scaffold"
python scripts/comfyui/bootstrap_submodule.py
git commit -m "Add pinned ComfyUI submodule"
```

When cloning from GitHub after the submodule has been committed:

```bash
git clone --recurse-submodules <repo-url>
```

or:

```bash
git submodule update --init --recursive
```

ComfyUI has machine-specific PyTorch/GPU setup. Prepare its Python environment following upstream instructions, then install RetroModGen into that same interpreter:

```bash
python scripts/comfyui/install_project_into_comfy_python.py \
  --python <path-to-comfy-python>
```

Launch the pinned submodule using RetroModGen's runtime directory:

```bash
python scripts/comfyui/run.py --python <path-to-comfy-python>
```

Verify node discovery from another shell:

```bash
python scripts/comfyui/verify.py
```

The initial scaffold exposes three working custom nodes:

```text
RetroModGen • Load AssetSpec
RetroModGen • Load Profile
RetroModGen • Validate AssetSpec
```

The implementation plan expands this into geometry, texture, rigging/IK, animation, validation, preview, and export node families.

## Initial target profiles

- `quake1_prop`
- `quake1_monster`
- `quake2_prop`
- `quake2_character`
- later: `late90s_fps`, `retro_modern`

The starter profile budgets are art-direction defaults unless a field is explicitly documented as a native format hard limit.

## Rigging policy

For articulated assets:

```text
source mesh
  -> final low-poly topology + UVs
  -> TOPOLOGY FREEZE
  -> skeleton
  -> skin weights
  -> IK/control rig
  -> skeletal animation/retargeting
  -> rigged GLB (canonical editable/runtime asset)
  -> optional vertex-frame bake
  -> MDL/MD2
```

Do not simplify or retopologize after binding without invalidating and regenerating the rig.

## Documentation

Start with:

- `docs/IMPLEMENTATION_PLAN.md` — action-by-action build plan with tests, verification, tool usage, and starter prompts.
- `docs/COMFYUI_INTEGRATION.md` — submodule/runtime/custom-node design and compatibility policy.
- `docs/ARCHITECTURE.md` — core boundaries and stage ownership.
- `docs/MDL_MD2_NOTES.md` — classic-format constraints and export notes.

## Current scaffold status

Implemented in the scaffold:

- `AssetSpec` parsing and profile validation;
- initial rigging fields in `AssetSpec`;
- backend/compiler/export boundaries;
- optional ComfyUI submodule bootstrap configuration;
- Comfy runtime base-directory layout;
- three offline-testable Comfy custom nodes;
- initial Comfy API workflow template;
- test/verification helpers.

Generation, mesh compilation, automatic rigging, IK, texture compilation, native-format exporters, and production Comfy workflows remain staged implementation work.
