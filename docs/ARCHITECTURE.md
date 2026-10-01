# retromodgen Architecture

## 1. Scope

`retromodgen` is an orchestration and compilation system for producing intentionally retro 3D game assets from modern generative models.

The system is split into five independently testable domains. ComfyUI is an optional but first-class authoring/inference surface around these domains:

1. **Intent** — convert a human request into `AssetSpec`.
2. **Generation** — obtain source images, source geometry, and source materials.
3. **Compilation** — deterministically transform generated content into a target visual/technical profile.
4. **Validation** — prove that a result satisfies profile and format constraints.
5. **Export/Preview** — emit assets and render them with the target presentation rules.

The LLM belongs in domain 1 and optionally in visual critique. It should not be required for deterministic compilation.

## 2. Top-level components

```text
                         +----------------------+
                         | Chat / CLI / Web UI  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | AssetSpec Builder    |
                         | LLM or manual input  |
                         +----------+-----------+
                                    |
                              AssetSpec.json
                                    |
                                    v
+-------------------+    +----------------------+    +-------------------+
| Reference Backend |--->| Pipeline Orchestrator|--->| Geometry Backend  |
| image / multiview |    +----------+-----------+    | Comfy/Hunyuan/etc |
+-------------------+               |                +-------------------+
                                    v
                             Generated source
                                    |
                                    v
                       +-------------------------+
                       | Retro Geometry Compiler |
                       +------------+------------+
                                    |
                                    v
                       +-------------------------+
                       | Retro Texture Compiler  |
                       +------------+------------+
                                    |
                                    v
                       +-------------------------+
                       | Animation Compiler      |
                       +------------+------------+
                                    |
                                    v
                       +-------------------------+
                       | Validators              |
                       +------------+------------+
                                    |
                       +------------+-------------+
                       |                          |
                       v                          v
                 modern GLB                  MDL / MD2
                       |                          |
                       +------------+-------------+
                                    v
                             preview renders
```

## 3. AssetSpec is the API boundary

Every generation request becomes an immutable-ish, serializable `AssetSpec` before expensive work starts.

Why:

- reproducibility;
- seed tracking;
- backend independence;
- easy caching;
- testable validation;
- easy comparison between candidate generations;
- straightforward future multiplayer/team workflows.

Backends do not receive free-form chat history. They receive a normalized `AssetSpec` plus explicit source images.

## 4. Pipeline stages

### Stage A — Spec resolution

Inputs:

- user description;
- selected profile;
- optional reference images;
- optional seed;
- user overrides.

Output: `AssetSpec`.

The LLM may fill defaults, but profile hard limits always win.

### Stage B — Reference generation

Optional. Produce a reconstruction-friendly concept sheet or multiview references.

Requirements should be backend-neutral:

- neutral pose;
- isolated object;
- consistent identity between views;
- stable proportions;
- minimal perspective distortion;
- no floor clutter;
- transparent or easily removable background.

### Stage C — Source 3D generation

A backend adapter executes one generator and returns a `GeneratedAsset` containing:

- source mesh path;
- source texture paths;
- backend metadata;
- seed/job IDs when available.

The source mesh may be very high resolution. That is acceptable.

### Stage D — Retro geometry compilation

Ordering:

1. mesh sanitation;
2. remove disconnected garbage according to thresholds;
3. orient/fix normals;
4. choose semantic importance weights if supplied;
5. simplify toward `target_triangles`;
6. enforce hard limit;
7. apply flat/hard-edge policy;
8. optional vertex-position quantization;
9. generate or repair UVs;
10. calculate error metrics.

The simplifier must stop if preserving a required feature would violate a hard error threshold. A failed compile is better than silently producing a bad asset.

### Stage E — Retro texture compilation

Recommended order:

1. retain high-resolution source material long enough to bake detail;
2. bake onto final low-poly UV layout;
3. edge-aware/detail-aware downsample;
4. optional contrast shaping;
5. palette conversion;
6. dithering;
7. save indexed or RGB target texture;
8. record nearest-neighbor sampling intent.

PBR channels are source information, not necessarily output information.

### Stage F — Animation compilation

For animated characters:

1. freeze final low-poly topology;
2. rig that topology;
3. author/retarget skeletal animation;
4. evaluate clips at selected frame rate;
5. bake evaluated positions to per-frame vertex arrays;
6. verify vertex index stability;
7. export modern skeletal and/or native vertex-frame format.

Do not simplify or retopologize after vertex animation has been baked.

### Stage G — Validation

Validation is layered:

- `AssetSpec` schema validation;
- profile validation;
- generic mesh validation;
- target-format validation;
- visual heuristic validation.

Examples:

- triangle count;
- vertex count;
- frame count;
- texture dimensions;
- UV range;
- degenerate triangles;
- non-finite positions;
- fixed topology across animation;
- format quantization error;
- file size budget.

### Stage H — Preview and critique

Render deterministic turntables with a small target-style preview renderer.

A vision model may critique:

- silhouette readability;
- generated-detail mush;
- texture readability at native resolution;
- face/weapon legibility;
- whether the asset looks modern despite satisfying numeric limits.

The critic proposes a new `AssetSpec` or compiler parameter set. It does not directly mutate binary geometry.

## 5. Caching

Every expensive stage should eventually be cacheable by a content hash:

```text
hash(
    stage_version,
    AssetSpec relevant fields,
    input file hashes,
    backend identifier,
    backend model version,
    seed
)
```

Do not implement distributed caching initially. A local content-addressed cache is enough.

## 6. Backend abstraction

`GeometryBackend.generate()` is deliberately narrow.

Backends may be:

- ComfyUI workflow submission;
- direct Hunyuan Python API;
- direct TRELLIS service;
- Stability/other local inference;
- remote proprietary API;
- manually supplied mesh.

The Retro Compiler cannot depend on a specific backend's internal mesh representation. Normalize to file or a common in-memory `MeshData` structure at the boundary.

## 7. Native code boundary

Start with Python/trimesh/PyMeshLab/xatlas-type tooling.

Move an operation into `native/` only after profiling demonstrates that it matters or when deterministic control is unavailable from existing libraries.

Expected first native component:

**weighted quadric-error mesh simplifier** with:

```text
collapse_cost =
    geometric_error
  + Wsilhouette * silhouette_error
  + Wsharp      * sharp_edge_error
  + Wuv         * uv_seam_error
  + Wsemantic   * semantic_importance
```

Implement scalar correctness first. SIMD is an optimization milestone, not an initial requirement.

## 8. Process architecture

Initial deployment can remain local:

```text
                         +---------------------+
                         |   ComfyUI node UI   |
                         | retromodgen_comfy   |
                         +----------+----------+
                                    |
                                    v
retromodgen CLI / API -------> RetroModGen core library
        |                           |
        +---- HTTP/WS ----> ComfyUI submodule :8188
        |                    (generation workflows)
        |
        +---- process -----> Blender headless (only where needed)
        |
        +---- library -----> mesh/texture/rigging compiler
```

ComfyUI runs from the optional `third_party/ComfyUI` Git submodule and should be launched with `--base-directory <repo>/.comfy` so its models/input/output/custom-node runtime remains outside the submodule checkout. See `docs/COMFYUI_INTEGRATION.md`.

Do not turn each stage into a microservice initially.

## 9. Failure policy

Every pipeline stage produces a machine-readable result with:

- status;
- warnings;
- errors;
- input hashes;
- output paths;
- statistics;
- elapsed time;
- implementation version.

No stage should silently clamp an engine hard limit. If a requested 6,000-triangle model is being exported to an MD2 profile with a 4,096-triangle limit, validation fails unless the compiler successfully gets under the limit.

## 10. Versioning

Version independently:

- `AssetSpec` schema;
- profiles;
- compiler algorithms;
- backend workflow templates;
- exporter implementations.

This is necessary to reproduce an asset months later after models or workflows change.
