# Retro Compiler Design

The Retro Compiler is the differentiating component of `retromodgen`.

## 1. Geometry compiler

### 1.1 Sanitation

Before simplification:

- remove non-finite vertices;
- detect degenerate triangles;
- optionally remove very small disconnected islands;
- weld only where safe;
- normalize scale/origin according to asset type;
- preserve material and UV boundaries.

### 1.2 Simplification

Initial implementation may use an existing simplifier for the proof of concept.

Target implementation: weighted QEM edge collapse.

Base quadric geometric error is augmented by feature penalties:

```text
C(edge) = Q(edge)
        + Ws * S(edge)
        + Wh * H(edge)
        + Wu * U(edge)
        + Wm * M(edge)
```

Where:

- `Q` = geometric quadric error;
- `S` = silhouette importance;
- `H` = hard/sharp edge penalty;
- `U` = UV seam/material-boundary penalty;
- `M` = semantic importance.

### 1.3 Silhouette preservation

A view-independent approximation can initially weight:

- boundary edges;
- high-curvature edges;
- convex/concave feature edges.

A stronger later implementation samples canonical views and marks edges contributing strongly to rendered silhouettes.

For characters, canonical views should include front, back, left, right, and two 3/4 views.

### 1.4 Retro topology character

The compiler should not optimize only for minimum geometric error. Late-1990s assets frequently benefit from:

- large planar polygons represented by visibly triangulated surfaces;
- hard changes in direction at joints;
- intentionally simplified fingers/hands;
- weapon silhouettes spending more triangles than hidden torso surfaces;
- asymmetry where it improves readability.

A future “retro topology regularizer” can discourage dense clusters of tiny triangles and prefer a more even coarse tessellation, but it should not be Phase 1.

### 1.5 Vertex quantization

Optional position quantization can be applied after simplification and before final validation.

Quantization parameters must be recorded so visual regression tests are reproducible.

## 2. UV compiler

Requirements:

- predictable islands;
- limited seam count;
- reasonable texel density;
- no accidental mirrored text/features unless requested;
- padding appropriate to tiny textures;
- optional classic format rules.

Tiny 128x128 skins make wasted UV space expensive. Packing quality matters more than it would on a 2K texture.

## 3. Texture compiler

### Source philosophy

Generate or paint source detail at a resolution higher than the final output. Use that information to produce a readable tiny texture.

### Proposed pipeline

```text
source PBR / RGB material
       |
       v
bake to final low-poly UV
       |
       v
feature-aware resampling
       |
       v
local contrast / edge reinforcement
       |
       v
palette mapping
       |
       v
dithering
       |
       v
128x128 or 256x256 final skin
```

### Detail-aware reduction

Naive downsampling can turn generated scratches/details into noise. Before reducing resolution:

- identify large color regions;
- retain major value boundaries;
- attenuate sub-pixel high-frequency detail;
- optionally sharpen only important boundaries;
- preserve facial/weapon markings through semantic masks.

## 4. Palettes

Palette handling should be a generic interface:

```text
Palette
  - colors[]
  - reserved_indices[]
  - transparency policy
  - nearest-color metric
```

Do not couple palette conversion directly to Quake code.

Supported metrics can include:

- RGB Euclidean;
- linear RGB;
- CIE Lab / perceptual distance.

## 5. Animation compiler

Use a modern skeletal working representation. Native classic formats are export targets.

Invariant before baking:

```text
vertex_count(frame N) == vertex_count(frame 0)
triangle_indices(frame N) == triangle_indices(frame 0)
```

Each clip is sampled at a profile/user-selected FPS and concatenated or grouped according to exporter rules.

## 6. Validation metrics

Each compile should emit:

```text
source_triangles
output_triangles
source_vertices
output_vertices
simplification_ratio
max_surface_error
rms_surface_error
uv_occupancy
texture_palette_size
animation_frame_count
format_quantization_error
```

Use these as both diagnostics and future training/optimization data.
