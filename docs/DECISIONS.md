# Architecture Decision Log

## ADR-001: Compiler-first architecture

**Decision:** Treat generated 3D as source material and make retro conversion a separate deterministic compiler.

**Reason:** “low poly” prompting does not guarantee target topology, palette, texture size, shading, or native format constraints.

## ADR-002: AssetSpec is canonical

**Decision:** Pipeline stages receive a structured `AssetSpec`, not raw chat transcripts.

**Reason:** reproducibility, caching, model independence, testability.

## ADR-003: ComfyUI is a first-class authoring/inference surface, not the owner of core logic

**Decision:** Support both ComfyUI custom nodes and HTTP/WebSocket workflow execution, while keeping compiler/rigging/export business logic in `retromodgen`.

**Reason:** users gain the power of ComfyUI's node editor without coupling deterministic compiler behavior to one UI/runtime. Direct/model-service backends and headless builds remain possible.

## ADR-006: ComfyUI source is an optional pinned Git submodule

**Decision:** Track ComfyUI at `third_party/ComfyUI` as a Git submodule, record the integration baseline in `config/comfyui.lock.json`, and launch it with `--base-directory <repo>/.comfy`.

**Reason:** this keeps upstream source/history separate, makes upgrades explicit/reversible, prevents runtime/model files from dirtying the submodule, and allows the core repository to function without ComfyUI initialized.

## ADR-004: Python orchestration, narrow native boundary

**Decision:** Python owns pipeline/control code. C++ is introduced only for measured performance-sensitive geometry operations.

**Reason:** faster iteration and simpler integrations while retaining a path to high-performance mesh processing.

## ADR-005: Skeletons internally, vertex frames at export

**Decision:** Character authoring uses skeletal animation; fixed-topology frames are baked late.

**Reason:** modern animation tooling is substantially easier while still supporting classic formats.
