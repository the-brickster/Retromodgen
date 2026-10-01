# AssetSpec

`AssetSpec` is the normalized request consumed by the pipeline.

## Goals

- serializable JSON;
- human-readable;
- stable enough for caching and automation;
- model-neutral;
- explicit retro constraints;
- easy for an LLM to generate;
- safe for deterministic validation.

## Important distinction

A **profile** supplies defaults and hard constraints. An **AssetSpec** supplies the request for one asset.

Example:

```text
profile = quake2_character
profile hard limit = 4096 triangles
AssetSpec target = 900 triangles
AssetSpec soft/hard generation ceiling = 1600 triangles
```

The compiler targets 900. It may accept up to 1600 if the chosen policy permits. It may never produce an MD2 result that violates the profile's true hard limits.

## Semantic weights

`geometry.semantic_weights` lets either a user or vision stage describe what should survive simplification.

Suggested keys:

```text
silhouette
face
eyes
mouth
hands
weapon
logo
accessory
large_flat_surface
discardable_detail
```

Weights are not universal semantics. They are compiler hints and should be interpreted through masks or per-vertex/triangle importance data when available.


## Rigging

Articulated characters, creatures, and mechanical assets use `rigging` to describe the authoring/runtime rig policy. The skeletal representation is canonical; legacy vertex-frame formats are export bakes.

Starter fields:

```json
{
  "rigging": {
    "mode": "skeletal",
    "auto_rig": true,
    "backend": "auto",
    "max_influences_per_vertex": 4,
    "generate_ik_controls": true,
    "preserve_authoring_rig": true,
    "topology_freeze_required": true
  }
}
```

Rules:

- topology-changing operations happen before binding unless the rig is explicitly invalidated/regenerated;
- deform bones + skin weights are the portable runtime contract;
- IK targets, pole targets, helper bones, and constraints are authoring controls and may be preserved separately from GLB;
- `animation.type = "skeletal"` is preferred for canonical character assets even when `md2`/`mdl` is also requested; the legacy exporter bakes evaluated skeletal motion to vertex frames.

## Reproducibility

Future schema revisions should add:

- `reference_generation.seed`;
- `geometry_generation.seed`;
- `backend.model_id`;
- `backend.model_revision`;
- `workflow_revision`;
- source image hashes;
- compiler version.

Do not put API keys or secrets in `AssetSpec`.
