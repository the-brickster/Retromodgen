# Roadmap

## Phase 0 — Repository and contracts

Status: scaffolded.

Deliverables:

- `AssetSpec` Pydantic schema;
- profile files;
- backend interface;
- compiler/exporter interfaces;
- basic profile validator;
- CLI validation command;
- architecture documentation.

Exit criterion: example AssetSpecs validate deterministically.

## Phase UI — ComfyUI authoring surface

Target: make RetroModGen available as a node-based authoring toolkit without coupling the core compiler to ComfyUI.

Deliverables:

- pinned `third_party/ComfyUI` Git submodule;
- `.comfy` base-directory runtime layout;
- `retromodgen_comfy` custom-node package;
- spec/profile/validation nodes;
- incremental geometry/texture/rigging/export node adapters;
- versioned API/UI workflow templates;
- offline node-contract tests and opt-in live compatibility tests.

Acceptance test:

> Launch the pinned ComfyUI checkout, see RetroModGen nodes in the editor, run a no-GPU AssetSpec/profile validation graph, and verify the same result through the core CLI.

## Phase 1 — First end-to-end static prop

Target: prove the visual pipeline before animation.

Deliverables:

- ComfyUI workflow submission/collection;
- ComfyUI source-generation graph feeding RetroModGen compiler nodes;
- one supported image-to-3D backend;
- mesh import normalization;
- existing-library mesh decimation;
- final UV generation or preservation;
- texture bake;
- 128x128 reduction;
- indexed/RGB palette quantization;
- GLB export;
- turntable preview.

Acceptance test:

> Given one reference image of an industrial crate, produce a validated `quake2_prop` GLB at the requested triangle/texture budget without manual Blender work.

## Phase 2 — Retro geometry compiler

Deliverables:

- deterministic mesh sanitation;
- weighted QEM scalar implementation;
- silhouette weighting;
- UV seam and hard-edge preservation;
- semantic importance masks;
- simplification error metrics;
- native C++ binding only after Python proof is stable.

Acceptance test:

> Against a fixed source-mesh corpus, the weighted simplifier produces repeatable output and preserves marked semantic regions better than uniform QEM at the same triangle budget.

## Phase 3 — Retro texture compiler

Deliverables:

- robust baking pipeline;
- detail-aware downsampling;
- palette abstraction;
- ordered and error-diffusion dithering;
- Quake-family palette loaders supplied from user-owned/install sources as appropriate;
- native-resolution preview.

Acceptance test:

> 128x128 results remain readable when rendered at target distance and do not merely look like blurred high-res textures.

## Phase 4 — Native Quake formats

Deliverables:

- MDL reader/writer tests;
- MD2 reader/writer tests;
- hard-limit validators;
- quantization-error reporting;
- regression corpus with round-trip tests.

Acceptance test:

> Exported reference assets load in compatible viewers/engines and round-trip without topology corruption.

## Phase 5 — Characters, skeletal rigs, IK, and animation

Deliverables:

- fixed-topology character workflow;
- auto-rig backend abstraction/integration;
- normalized skin weights + deformation QA;
- deform skeleton as canonical runtime representation;
- IK/control-rig generation for authoring;
- animation retarget/import path;
- rigged GLB round-trip validation;
- skeletal-to-vertex-frame baker;
- clip naming/ranges;
- GLB + MDL/MD2 dual export;
- equivalent ComfyUI rigging/animation node path.

Acceptance test:

> One generated humanoid is simplified, topology-frozen, bone-rigged, skin-weighted, given usable arm/leg IK controls, animated/retargeted, exported as a working rigged GLB, and optionally baked to one native vertex-frame format from the same canonical skeleton/topology.

## Phase 6 — LLM/vision authoring loop

Deliverables:

- request -> AssetSpec agent;
- candidate generation;
- deterministic contact sheet/turntable renders;
- vision critique into structured changes;
- candidate comparison data;
- user approval checkpoint.

The LLM proposes changes; deterministic compiler code performs them.

## Phase 7 — Dataset and optional training

Before training any generator, collect:

- source prompt;
- normalized spec;
- source references;
- backend/model/version;
- generated source asset;
- compiler parameters;
- final asset;
- user-selected candidate;
- manual edits;
- validation metrics.

Only fine-tune when the stored data demonstrates a repeated failure that preprocessing/compiler rules cannot solve.

## Explicit non-goals for early versions

- custom diffusion training;
- distributed microservices;
- cloud scheduler;
- multi-user permissions;
- procedural level generation;
- fully automatic production-quality rigging for every topology;
- perfect MDL/MD2 support before the GLB retro compiler works.
