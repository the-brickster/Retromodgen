# ComfyUI Integration Design

## 1. Goal

ComfyUI is a first-class authoring surface for RetroModGen, but it is not the owner of
RetroModGen's compiler logic.

The project supports **both directions of integration**:

1. **ComfyUI -> RetroModGen custom nodes** for interactive node-graph authoring.
2. **RetroModGen -> ComfyUI HTTP/WebSocket API** for CLI/headless automation.

Both routes call the same core RetroModGen library and operate on the same `AssetSpec`,
profiles, mesh/texture/rigging stages, validation, and exporters.

```text
                   interactive authoring
                        ComfyUI UI
                            |
                    RetroModGen nodes
                            |
                            v
+-------------------- RetroModGen core --------------------+
| AssetSpec | compiler | rigging | validation | exporters |
+---------------------------------------------------------+
                            ^
                            |
                  CLI/API orchestrator
                            |
                   ComfyUI HTTP / WS
                            |
                   generation workflows
```

## 2. Why ComfyUI is a Git submodule

The preferred source-development layout is:

```text
retromodgen/
├── third_party/
│   └── ComfyUI/                 # Git submodule
├── .comfy/                      # RetroModGen-owned Comfy runtime base directory
│   └── custom_nodes/
│       └── retromodgen_comfy/   # tracked thin loader
├── src/
│   ├── retromodgen/             # core library
│   └── retromodgen_comfy/       # custom-node implementation
└── workflows/comfyui/           # versioned API/UI workflow templates
```

Benefits:

- upstream ComfyUI history stays intact;
- the parent repository records an exact ComfyUI commit;
- upgrading ComfyUI is an explicit reviewed change;
- ComfyUI can still be omitted for core development/CI;
- model weights are never stored in the RetroModGen repository;
- ComfyUI can be replaced by another backend later.

The scaffold records a baseline upstream commit in `config/comfyui.lock.json`.
Advancing that pin is a compatibility change and must pass the Comfy smoke suite.

ComfyUI is separately licensed under GPL-3.0. Keep its upstream license/history intact
and review distribution obligations before shipping a bundle that includes it.

## 3. Why use `--base-directory`

Do not install RetroModGen files into the ComfyUI submodule tree.

RetroModGen launches the ComfyUI submodule with:

```text
--base-directory <retromodgen>/.comfy
```

This causes Comfy runtime directories such as custom nodes, models, input, output, and
user data to live outside the submodule. The submodule remains clean and easy to update.

The tracked loader:

```text
.comfy/custom_nodes/retromodgen_comfy/__init__.py
```

re-exports node mappings from the installed `retromodgen_comfy` Python package.

## 4. Environment model

### Core development

No ComfyUI install is required:

```bash
python -m venv .venv
pip install -e ".[dev,mesh]"
pytest
```

### Comfy development

ComfyUI may use a separate Python environment because PyTorch/CUDA choices are machine
specific. Follow upstream ComfyUI setup for that environment, then install RetroModGen
editable into the same interpreter:

```bash
python scripts/comfyui/install_project_into_comfy_python.py \
  --python <path-to-comfy-python>
```

Set this interpreter when launching:

```text
RETROMODGEN_COMFY_PYTHON=<path-to-comfy-python>
```

or pass `--python` to `scripts/comfyui/run.py`.

## 5. Submodule bootstrap

When starting from the scaffold ZIP:

```bash
git init
git add .
git commit -m "Initial RetroModGen scaffold"
python scripts/comfyui/bootstrap_submodule.py
git commit -m "Add pinned ComfyUI submodule"
```

When cloning a repository that already contains the gitlink:

```bash
git clone --recurse-submodules <repo-url>
```

or:

```bash
git submodule update --init --recursive
```

The bootstrap script checks out the commit recorded in `config/comfyui.lock.json`.

## 6. Custom-node contract

Custom nodes must be **thin adapters**. A node may:

- collect editor parameters;
- translate Comfy values into core RetroModGen types;
- call one public core function/stage;
- return results and diagnostics in Comfy-friendly form.

A node must not contain a second implementation of:

- profile validation;
- mesh simplification;
- texture compilation;
- rigging/weight cleanup;
- IK solving;
- MDL/MD2 writing;
- cache/provenance rules.

Those belong in `src/retromodgen/` and are unit-tested independently.

## 7. Initial Comfy data types

Use explicit custom socket types for structured in-process objects:

```text
RETROMODGEN_ASSET_SPEC
RETROMODGEN_PROFILE
RETROMODGEN_MESH
RETROMODGEN_RIG
RETROMODGEN_ANIMATION
RETROMODGEN_VALIDATION_REPORT
```

Use standard Comfy types where interoperability matters:

```text
IMAGE
MASK
STRING
INT
FLOAT
BOOLEAN
```

File paths should be normalized by core functions before use. Do not rely on the process
working directory after the prototype stage.

## 8. Node families

### Spec/profile

- `RetroModGen_LoadAssetSpec`
- `RetroModGen_CreateAssetSpec`
- `RetroModGen_LoadProfile`
- `RetroModGen_ValidateAssetSpec`
- `RetroModGen_SaveAssetSpec`

### Geometry

- `RetroModGen_ImportMesh`
- `RetroModGen_NormalizeMesh`
- `RetroModGen_SimplifyMesh`
- `RetroModGen_QuantizeVertices`
- `RetroModGen_FreezeTopology`
- `RetroModGen_AnalyzeMesh`

### Texture

- `RetroModGen_BakeTexture`
- `RetroModGen_DownscaleTexture`
- `RetroModGen_QuantizePalette`
- `RetroModGen_DitherTexture`

### Rigging/animation

- `RetroModGen_AutoRig`
- `RetroModGen_GenerateSkinWeights`
- `RetroModGen_BuildIKControls`
- `RetroModGen_ValidateRig`
- `RetroModGen_ImportAnimation`
- `RetroModGen_RetargetAnimation`
- `RetroModGen_BakeVertexFrames`

### Validation/export/preview

- `RetroModGen_ValidateAsset`
- `RetroModGen_ExportGLB`
- `RetroModGen_ExportMD2`
- `RetroModGen_ExportMDL`
- `RetroModGen_RenderTurntable`

Only the first three spec/profile nodes are implemented in the scaffold. The remaining
nodes are action items in the implementation plan and must call core services rather
than duplicating them.

## 9. Rigging flow inside ComfyUI

The canonical editable animation representation remains skeletal:

```text
Generated mesh
   -> Retro normalize/simplify/UV
   -> Freeze topology
   -> AutoRig or imported skeleton
   -> Generate/clean skin weights
   -> Build IK/control rig
   -> Animation author/retarget
   -> Validate deformation
   -> Export rigged GLB
   -> optional bake to MDL/MD2 vertex frames
```

The deform skeleton is portable runtime data. IK targets, pole targets, helper bones,
and authoring constraints may be stored in a RetroModGen rig manifest or `.blend` file
when they cannot be represented directly in glTF.

## 10. Generation workflow integration

ComfyUI is responsible for inference-oriented steps such as:

- concept/reference generation;
- background removal;
- multiview generation;
- Hunyuan/TRELLIS/other source mesh generation;
- GPU model scheduling and offloading.

Generated geometry then crosses a clear boundary into RetroModGen nodes.

Example full graph:

```text
[Reference Image]
       |
[Background Removal]
       |
[Multiview / Conditioning]
       |
[Hunyuan/TRELLIS Source Mesh]
       |
[Retro Normalize Mesh]
       |
[Retro Simplify Mesh]
       |
[Retro UV / Texture Compile]
       |
+----------------------+----------------------+
|                                             |
static asset                               articulated asset
|                                             |
[Validate]                              [Freeze Topology]
|                                             |
[Export GLB]                           [Auto Rig + Weights]
                                              |
                                        [Build IK Controls]
                                              |
                                      [Animate / Retarget]
                                              |
                                     [Export Rigged GLB]
                                              |
                                      [optional MDL/MD2]
```

## 11. Versioned workflow policy

Keep committed workflow templates in `workflows/comfyui/`.

For every production workflow record:

- workflow ID/name;
- workflow schema/version;
- RetroModGen version;
- ComfyUI git commit;
- required custom node packages and versions;
- generation model/checkpoint identifiers;
- required inputs;
- expected outputs.

Do not commit model weights or machine-specific absolute paths.

## 12. Out-of-process API integration

The existing `ComfyUIBackend` remains useful for headless builds. At the baseline Comfy
commit, upstream exposes endpoints including:

```text
GET  /system_stats
GET  /object_info
GET  /ws
POST /prompt
GET  /history
```

Before relying on endpoint details in production code, inspect the pinned upstream
implementation and add contract tests around the payloads used by RetroModGen.

The API backend should:

1. resolve a versioned workflow template;
2. upload/resolve input assets;
3. submit the workflow;
4. observe completion via WebSocket or bounded polling fallback;
5. collect output file metadata;
6. copy/materialize outputs into the RetroModGen job directory;
7. attach Comfy workflow/model provenance to `GeneratedAsset`.

## 13. Offline tests

Comfy integration code must have tests that run without ComfyUI:

- node mapping import test;
- node input/output contract tests;
- AssetSpec load/validate node tests;
- workflow JSON schema/placeholder tests;
- HTTP client tests using mocked responses;
- workflow submission payload tests;
- graceful unavailable-server tests.

These are part of ordinary CI.

## 14. Live Comfy smoke test

The live test is opt-in and should never block contributors without a GPU/Comfy setup.

1. Initialize the submodule.
2. Prepare a valid Comfy Python environment using upstream instructions.
3. Install RetroModGen editable into that interpreter.
4. Start Comfy:

```bash
python scripts/comfyui/run.py --python <comfy-python>
```

5. In another shell:

```bash
python scripts/comfyui/verify.py
```

6. Verify `/object_info` reports at least:

```text
RetroModGen_LoadAssetSpec
RetroModGen_LoadProfile
RetroModGen_ValidateAssetSpec
```

7. Submit `workflows/comfyui/spec_validate.api.json` through the API client once B1 is
   implemented.
8. Later, execute one GPU-backed source-generation graph and one full retro compilation
   graph.

## 15. ComfyUI upgrade procedure

Never update the submodule just because upstream `master` changed.

1. Read current ComfyUI release notes/commits and identify relevant node/API changes.
2. Create a dedicated compatibility branch.
3. Update the submodule to the candidate commit.
4. Update `config/comfyui.lock.json`.
5. Run offline tests.
6. Launch Comfy and run `scripts/comfyui/verify.py`.
7. Run the API workflow smoke tests.
8. Run at least one real source-generation workflow if model nodes are affected.
9. Inspect the node graph manually for broken sockets/widgets.
10. Commit the new gitlink and lock file together.

Rollback is simply restoring the previous gitlink + lock file.

## 16. Tool-calling guidance for coding agents

When changing Comfy integration:

1. **GitHub/web lookup:** inspect the exact pinned ComfyUI source or official docs for the
   API/node behavior being changed. Do not assume old examples still match current Comfy.
2. **Repository tools:** inspect existing `retromodgen_comfy` nodes and workflow templates
   before adding new classes.
3. **Shell/container:** run focused unit tests and the full offline suite.
4. **Live integration:** only when a Comfy environment is available, launch the pinned
   submodule and verify `/system_stats` + `/object_info` before debugging workflows.
5. **Evidence:** record the Comfy commit, commands run, workflow used, and output/validation
   results in the completion summary.

A coding agent must not change the Comfy submodule pin as a side effect of unrelated work.
