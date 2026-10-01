# RetroModGen Implementation Plan

> Project: `retromodgen`  
> Goal: a model-agnostic harness and deterministic retro-asset compiler for creating low-poly game assets, including Quake 1 / Quake II style assets, with bone-based skeletal rigging as the canonical representation for generated characters, creatures, and articulated models.  
> Primary development rule: **ComfyUI and large generative models are optional adapters. The core compiler, validation, exporters, CLI, and tests must work without them.**

---

## 1. Purpose of this document

This is the execution plan for building RetroModGen from the current scaffold into a usable asset-generation and retro-compilation tool.

It is written so that a coding agent can take **one action item at a time**, inspect the repository, implement the requested work, run tests, verify the result, and leave the repository in a known-good state.

Every action item contains:

- objective;
- scope and likely files;
- implementation steps;
- required tests;
- manual/functional verification;
- completion/acceptance criteria;
- expected tool calls;
- a copy/paste **starter prompt** for a coding model.

The plan deliberately separates:

1. deterministic core functionality;
2. optional GPU/model generation backends;
3. retro geometry and texture compilation;
4. classic Quake format support;
5. animation;
6. LLM/vision orchestration.

---

# 2. Non-negotiable architecture rules

These rules apply to every action item.

## 2.1 ComfyUI is first-class but optional

ComfyUI is a supported **node-graph authoring surface** and **inference runtime**, but the RetroModGen core must remain independently usable and testable.

The following must work without ComfyUI installed or running:

- `AssetSpec` parsing;
- profile loading and validation;
- backend discovery;
- mock backend;
- mesh importing;
- mesh sanitation;
- simplification;
- UV processing;
- texture processing;
- rigging data/validation logic;
- GLB/OBJ output;
- MDL/MD2 support;
- validation;
- preview rendering where a local non-Comfy renderer is available;
- unit tests and most CI jobs.

RetroModGen supports two complementary Comfy paths:

```text
ComfyUI editor -> retromodgen_comfy custom nodes -> RetroModGen core
RetroModGen CLI/API -> ComfyUI HTTP/WebSocket -> generation workflows
```

The preferred source-development layout keeps ComfyUI as an optional Git submodule at `third_party/ComfyUI`. ComfyUI runtime data lives under `.comfy/` using `--base-directory`, so the submodule remains clean and upgradeable.

Comfy custom nodes must be **thin adapters** around core functions. The node graph may orchestrate RetroModGen stages, but the canonical implementation of simplification, texturing, rigging, validation, and export must stay in `src/retromodgen/`.

## 2.2 Backends receive normalized requests

Generation backends receive:

```text
AssetSpec
+ explicit reference files
+ backend configuration
```

They do not receive arbitrary chat history.

## 2.3 Generated source assets are not final assets

AI generation produces a **source asset**. The deterministic compiler produces the final retro asset.

```text
reference/prompt
    -> source generator
    -> raw mesh/material
    -> retro geometry compiler
    -> retro texture compiler
    -> optional topology freeze + bone rig/skin for articulated assets
    -> validation
    -> exporter
```

## 2.4 Deterministic stages must be reproducible

Given the same:

- input files;
- `AssetSpec`;
- compiler version;
- compiler options;

all deterministic compiler stages should produce equivalent results.

When bit-for-bit determinism is impractical, output metrics must still remain deterministic within documented tolerances.

## 2.5 Do not optimize before the reference implementation works

For complex algorithms:

1. implement the simplest correct scalar/reference version;
2. create regression tests;
3. profile it;
4. optimize only when justified.

This is especially important for the weighted QEM simplifier.

## 2.6 Never silently violate a profile

If a request cannot satisfy a hard profile constraint without exceeding an error threshold, fail with a useful diagnostic instead of silently returning a bad asset.

## 2.7 Bone rigs are canonical for articulated assets

Generated characters, creatures, and articulated mechanical assets must use a bone-based skeletal representation as the primary animation source. Static, non-articulated props may explicitly opt out with `rigging.mode = "none"`.

The pipeline must distinguish between:

```text
DEFORM RIG
  skeleton hierarchy
  bind pose / inverse bind matrices
  per-vertex joint indices and skin weights
  runtime animation clips

CONTROL RIG
  IK targets
  pole targets
  helper/control bones
  constraints
  animator-facing controls
```

The deform rig is the portable runtime contract. The control rig is an authoring layer and may contain Blender/internal features that are not representable in every runtime format.

The canonical character pipeline is therefore:

```text
source mesh
  -> final low-poly topology + UVs
  -> TOPOLOGY FREEZE
  -> skeleton generation/import
  -> skin-weight generation
  -> rig validation
  -> IK/control-rig generation
  -> skeletal animation/retargeting
  -> skeletal GLB export
  -> optional skeletal-to-vertex-frame bake
  -> MDL/MD2 export
```

Topology-changing operations are forbidden after binding unless a stage explicitly invalidates and regenerates the rig.

For glTF/GLB, the required portable data is the skin/joint hierarchy, inverse bind matrices, `JOINTS_n`/`WEIGHTS_n`, and animation channels. Generic Blender-style IK constraints are not part of the core glTF 2.0 skin/animation contract, so IK/control-rig state must be preserved separately when needed (for example in an authoring `.blend` or RetroModGen rig manifest), while runtime animations may be baked to the deform bones.

Implementation references to verify when this phase begins:

- Khronos glTF 2.0 specification — skins, joints, inverse bind matrices, `JOINTS_n`, `WEIGHTS_n`, animation channels: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- Blender armatures/skinning/IK documentation: https://docs.blender.org/manual/en/4.5/animation/armatures/
- VAST-AI-Research SkinTokens / TokenRig (current automatic skeleton + skinning candidate): https://github.com/VAST-AI-Research/SkinTokens
- VAST-AI-Research UniRig (alternative/reference auto-rigging backend): https://github.com/VAST-AI-Research/UniRig

Do not make either TokenRig or UniRig a hard dependency of RetroModGen core.

---

# 3. Agent/tool usage policy

The following tool behavior should be included in every implementation task.

## 3.1 Repository inspection

Before modifying code:

1. inspect the current repository tree;
2. read the relevant architecture/roadmap documents;
3. inspect existing interfaces before introducing new abstractions;
4. search for existing implementations before adding duplicate helpers.

Recommended tool calls:

```text
GitHub repository/file search       when operating on the remote repository
shell/container tree/search         when a local checkout is available
```

Do not assume the scaffold has not changed.

## 3.2 External documentation

Use current upstream documentation when implementing integration points or binary formats.

Examples:

- ComfyUI API behavior;
- Hunyuan/TRELLIS workflow nodes;
- trimesh/PyMeshLab/xatlas APIs;
- glTF behavior;
- Quake MDL/MD2 structures;
- Blender command-line behavior.

Tool rule:

```text
Use web/GitHub search for current upstream behavior.
Prefer official repositories and documentation.
Record any compatibility assumption in docs or code comments.
```

Do **not** browse merely to implement ordinary local code whose API is already known and tested.

## 3.3 Local execution

For implementation tasks, the agent should use shell/container execution to:

- install the project in editable mode when needed;
- run focused tests first;
- run the full test suite before completion;
- invoke the CLI manually for relevant acceptance tests;
- inspect generated output files;
- run formatting/lint/type checks configured by the project.

## 3.4 GitHub operations

When direct repository write access is available:

1. create/use a feature branch unless instructed otherwise;
2. make coherent commits;
3. do not rewrite unrelated code;
4. include tests with behavior changes;
5. summarize files changed and commands run;
6. open a PR when that is the selected workflow.

Suggested branch naming:

```text
feat/backend-registry
feat/mock-backend
feat/comfyui-backend
feat/mesh-normalization
feat/retro-textures
feat/qem-simplifier
feat/md2-export
```

## 3.5 Verification rule

A coding agent must not say an item is complete simply because code was written.

Completion requires evidence from commands such as:

```text
pytest
retromodgen ...
cmake --build ...
known-file roundtrip verification
generated artifact inspection
```

If a required external dependency is unavailable, the agent must:

1. complete all dependency-independent work;
2. provide automated mocks/fixtures;
3. clearly mark the blocked integration test;
4. provide the exact command to run when the dependency becomes available.

---

# 4. Recommended local development environments

## 4.1 Core development environment

This environment should support most work:

```text
Windows 10/11 or Linux
Python 3.12+
Git
CMake
MSVC or Clang/GCC
```

Typical setup:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,mesh]"
pytest
```

## 4.2 Optional ComfyUI/inference environment

For source development, ComfyUI should normally be initialized as the pinned Git submodule:

```text
third_party/ComfyUI/
```

Runtime data is redirected outside the submodule:

```text
.comfy/
  custom_nodes/
  models/
  input/
  output/
  user/
```

Bootstrap from the scaffold:

```bash
python scripts/comfyui/bootstrap_submodule.py
```

ComfyUI may use a separate Python environment because PyTorch/CUDA choices are machine-specific. Install RetroModGen editable into that interpreter:

```bash
python scripts/comfyui/install_project_into_comfy_python.py --python <comfy-python>
```

Launch the pinned submodule with the RetroModGen base directory:

```bash
python scripts/comfyui/run.py --python <comfy-python>
```

Verify discovery:

```bash
python scripts/comfyui/verify.py
```

Default local endpoint:

```text
http://127.0.0.1:8188
```

A developer may instead point the HTTP backend at another ComfyUI machine. The core library must not care where ComfyUI runs.

## 4.3 Optional Blender environment

Blender should be treated as a command-line worker rather than an embedded Python dependency.

Example invocation:

```bash
blender --background --python tools/blender/render_turntable.py -- input.glb output_dir
```

---

# 5. Definition of Done for an action item

An action item is complete only when all applicable conditions are true:

- implementation exists;
- focused unit tests pass;
- regression tests are added for bugs discovered during development;
- full test suite passes;
- relevant CLI/API path was manually exercised;
- output validation passes;
- documentation is updated when behavior/configuration changed;
- optional integrations fail gracefully when unavailable;
- no unrelated refactor was introduced;
- completion summary lists the commands actually run.

---

# 6. Implementation sequence

The recommended order is:

```text
Phase A: core developer experience
  A1 dependency groups
  A2 backend registry/config
  A3 mock backend + fixtures
  A4 orchestrator
  A5 CLI

Phase UI: ComfyUI authoring/integration track
  UI1 pinned Git submodule + runtime layout
  UI2 custom-node package and node contracts
  UI3 spec/profile/validation nodes
  UI4 compiler/rigging/export node adapters
  UI5 versioned workflows and graph UX
  UI6 offline/live compatibility harness

Phase B: first end-to-end static asset
  B1 ComfyUI client
  B2 first real geometry workflow
  B3 mesh normalization
  B4 baseline simplification
  B5 retro texture compiler
  B6 GLB export + preview + validation

Phase C: purpose-built retro compiler
  C1 weighted QEM reference implementation
  C2 silhouette / UV / hard-edge weighting
  C3 semantic weighting
  C4 native C++ implementation

Phase D: classic formats
  D1 MD2
  D2 MDL

Phase E: characters, bone rigs, IK, and animation
  E1 rigging data model + topology-freeze contract
  E2 rigging backend abstraction + backend evaluation spike
  E3 automatic skeleton generation and semantic bone mapping
  E4 skin-weight generation + deformation QA
  E5 IK/control-rig generation
  E6 skeletal animation import/retargeting
  E7 skeletal GLB export + rig round-trip validation
  E8 skeletal-to-vertex-frame bake for MDL/MD2

Phase F: AI authoring loop
  F1 request -> AssetSpec
  F2 visual critique

Phase G: production hardening
  G1 cache/provenance
  G2 CI matrix
  G3 benchmark/regression corpus
  G4 packaging/releases
```

---

# 7. Action items

## A1 — Finalize dependency groups and developer bootstrap

### Objective

Ensure a fresh checkout can be developed and tested without ComfyUI, Blender, Hunyuan, TRELLIS, CUDA, or model weights.

### Likely files

```text
pyproject.toml
README.md
docs/ARCHITECTURE.md
.env.example
```

### Implementation steps

1. Audit current required Python dependencies.
2. Keep the default dependency set minimal.
3. Add/normalize optional extras:
   - `dev`;
   - `mesh`;
   - `comfy` if client-only packages are needed;
   - `all` as a convenience meta-extra where practical.
4. Do not add ComfyUI itself as a dependency.
5. Document supported Python version.
6. Add concise local setup instructions.
7. Ensure importing `retromodgen` has no optional GPU/model imports.

### Tests

Run in a clean virtual environment:

```bash
pip install -e ".[dev]"
python -c "import retromodgen"
pytest
```

Then:

```bash
pip install -e ".[dev,mesh]"
pytest
```

### Verification

Verify the following does **not** occur during import:

- torch import;
- CUDA initialization;
- ComfyUI import;
- model downloads;
- network access.

### Acceptance criteria

- core package installs without ComfyUI;
- test suite passes;
- optional mesh packages install separately;
- README clearly states ComfyUI is optional.

### Expected tool calls

- inspect `pyproject.toml` and imports;
- shell commands for clean install/test;
- web only if an uncertain dependency version/API must be confirmed.

### Starter prompt

```text
Work on RetroModGen action item A1: finalize dependency groups and developer bootstrap.

First inspect the repository, pyproject.toml, imports, README, and architecture docs. Keep ComfyUI, PyTorch model stacks, Blender, Hunyuan, and TRELLIS optional. A normal `pip install -e ".[dev]"` must let a developer import retromodgen and run the core tests without GPU/model software.

Implement the smallest clean dependency structure, update setup documentation, and add any regression tests needed to prove optional packages are not imported by the core. Run the clean-install/import test and the full test suite. Do not claim completion without showing the commands and results.
```

---

## A2 — Backend registry and configuration system

### Objective

Allow generation backends to be selected without hard-coded imports or conditionals spread through the pipeline.

### Likely files

```text
src/retromodgen/backends/base.py
src/retromodgen/backends/registry.py
src/retromodgen/config.py
src/retromodgen/backends/__init__.py
tests/test_backend_registry.py
```

### Implementation steps

1. Review the existing `GeometryBackend` interface.
2. Define a stable backend identifier, e.g. `mock`, `comfyui`.
3. Implement a registry/factory with lazy imports.
4. Add configuration for backend-specific settings.
5. Read defaults from explicit config/environment variables without global side effects.
6. Produce a useful error for unavailable optional backends.
7. Add a `list_backends()` facility that distinguishes registered vs available.

### Tests

Test:

- mock backend lookup;
- unknown backend error;
- optional backend module missing;
- backend configuration override;
- lazy import behavior.

```bash
pytest tests/test_backend_registry.py -q
pytest
```

### Verification

```bash
python -c "from retromodgen.backends.registry import list_backends; print(list_backends())"
```

The command should work without ComfyUI installed.

### Acceptance criteria

No pipeline code should need constructs such as:

```python
if backend == "comfy":
    ...
elif backend == "hunyuan":
    ...
```

Backend selection belongs in one registry/factory boundary.

### Expected tool calls

- repository search for backend construction;
- shell/unit test execution;
- no external web call normally required.

### Starter prompt

```text
Implement RetroModGen action item A2: backend registry and configuration.

Inspect the existing GeometryBackend interface and pipeline first. Add a small lazy backend registry/factory so core code can select `mock`, `comfyui`, and future backends without importing GPU/model packages at module import time. Add focused tests for lookup, unknown backends, availability reporting, and optional dependency failure. Keep the design simple and do not introduce plugin-framework overengineering.

Run the focused tests and the full suite, then show the exact verification commands and results.
```

---

## A3 — Deterministic MockGeometryBackend and test fixture corpus

### Objective

Make the entire pipeline developable and testable without an inference server.

### Likely files

```text
src/retromodgen/backends/mock.py
tests/assets/
tests/test_mock_backend.py
```

### Implementation steps

1. Add `MockGeometryBackend` implementing the real backend contract.
2. Create small legally redistributable/generated fixture meshes:
   - cube/box prop;
   - low-poly asymmetric prop;
   - malformed mesh fixture where useful.
3. Make backend results deterministic by spec/fixture name.
4. Return realistic metadata fields used by real backends.
5. Never require a network connection.

### Tests

- same request returns same fixture and metadata;
- references are accepted/recorded according to interface rules;
- missing fixture returns deterministic error;
- generated asset object can pass into the orchestrator.

### Verification

Run:

```bash
retromodgen generate examples/quake2_guard.asset.json --backend mock --output build/mock
```

If the full generate command is not implemented yet, use a temporary focused Python invocation and implement the CLI in A5.

### Acceptance criteria

CI can exercise generation-to-compiler wiring with no GPU.

### Expected tool calls

- shell to create/generate fixtures;
- unit tests;
- file inspection;
- no web requirement.

### Starter prompt

```text
Implement RetroModGen action item A3: deterministic MockGeometryBackend and fixture corpus.

Read the backend contract and AssetSpec model before coding. Add a mock backend that behaves like a real source-geometry backend but returns small deterministic local fixtures. The fixtures must be suitable for CI and must not depend on network access, ComfyUI, PyTorch, CUDA, or Blender.

Add unit tests proving determinism and compatibility with the generated-asset contract. Run the focused tests and full suite and report the commands/results.
```

---

## A4 — Pipeline orchestrator with explicit stage boundaries

### Objective

Turn the current placeholder orchestrator into a deterministic pipeline coordinator.

### Target stage model

```text
spec resolution
  -> source generation
  -> geometry normalization
  -> geometry compile
  -> texture compile
  -> validation
  -> export
  -> preview metadata
```

### Likely files

```text
src/retromodgen/pipeline/orchestrator.py
src/retromodgen/pipeline/results.py
src/retromodgen/compiler/interfaces.py
tests/test_orchestrator.py
```

### Implementation steps

1. Define explicit input/output dataclasses or Pydantic models for stage results.
2. Keep filesystem paths explicit.
3. Do not hide temporary files in process-global directories.
4. Propagate source/backend metadata into the final manifest.
5. Stop on validation failure.
6. Add stage-level errors with enough context to identify the failing stage.
7. Initially use no-op/reference compiler components where real compilers are not yet implemented.

### Tests

Use the mock backend to test:

- successful stage ordering;
- exception propagation;
- validation failure halts export;
- backend metadata survives through the pipeline;
- output directory structure is deterministic.

### Verification

Generate a pipeline manifest from the mock backend and manually inspect it.

Expected structure:

```text
build/<job>/
  manifest.json
  source/
  compiled/
  preview/
```

### Acceptance criteria

The orchestrator itself contains no ComfyUI-specific logic.

### Expected tool calls

- repo inspection;
- shell/test execution;
- JSON/file inspection.

### Starter prompt

```text
Implement RetroModGen action item A4: pipeline orchestrator with explicit stage boundaries.

Inspect the current orchestrator, backend interface, compiler interfaces, validation code, and AssetSpec. Implement a simple deterministic coordinator that runs generation -> geometry -> texture -> validation -> export using injected interfaces. Use the mock backend in tests. Do not put ComfyUI-specific code in the orchestrator.

Add failure-path tests and verify the pipeline produces a deterministic job directory/manifest. Run focused tests and the full suite before finishing.
```

---

## A5 — CLI commands and configuration UX

### Objective

Provide a stable command line suitable for developers, CI, and future agents.

### Initial commands

```text
retromodgen profiles
retromodgen validate <asset-spec>
retromodgen backends
retromodgen generate <asset-spec> --backend <name> --output <dir>
retromodgen compile <mesh> --profile <profile> --output <dir>
retromodgen inspect <asset>
```

### Implementation steps

1. Preserve current commands where compatible.
2. Add structured nonzero exit codes for failure.
3. Keep human-readable output concise.
4. Add optional `--json` output for automation.
5. Do not require model dependencies merely to invoke `--help`.
6. Expose backend availability.

### Tests

Use CLI test helpers/subprocess tests for:

- help;
- list profiles;
- validate known-good spec;
- reject invalid spec;
- list backends;
- generate with mock backend;
- unavailable Comfy backend error.

### Verification

```bash
retromodgen --help
retromodgen profiles
retromodgen backends
retromodgen validate examples/quake2_guard.asset.json
retromodgen generate examples/quake2_guard.asset.json --backend mock --output build/mock
```

### Acceptance criteria

All listed commands either work or clearly report “not implemented” only for deliberately deferred compiler stages. No traceback should be shown for normal user errors unless debug mode is enabled.

### Expected tool calls

- shell to exercise CLI;
- no web normally required.

### Starter prompt

```text
Implement RetroModGen action item A5: CLI and configuration UX.

Inspect the current CLI and existing project models first. Implement/normalize commands for profiles, validate, backends, generate, compile, and inspect. The CLI must import and show help without ComfyUI/PyTorch/model packages installed. Add useful nonzero exit codes and optional JSON output where straightforward.

Use the mock backend for end-to-end CLI tests. Run the exact manual commands listed in the implementation plan plus pytest, and report the results.
```

---

# Phase UI — ComfyUI authoring and integration track

This track can begin after A2/A3 and proceeds in parallel with the compiler. It establishes ComfyUI as a first-class editor without making it a hard dependency of RetroModGen core.

## UI1 — Pin ComfyUI as an optional Git submodule and isolate runtime state

### Objective

Make ComfyUI reproducible for source development while keeping upstream source, runtime files, model weights, and RetroModGen code cleanly separated.

### Likely files

```text
.gitmodules
config/comfyui.lock.json
third_party/README.md
scripts/comfyui/bootstrap_submodule.py
scripts/comfyui/run.py
.comfy/
docs/COMFYUI_INTEGRATION.md
```

### Implementation steps

1. Record the upstream ComfyUI repository URL, branch, baseline commit, and date in `config/comfyui.lock.json`.
2. Define `third_party/ComfyUI` in `.gitmodules`.
3. Provide a bootstrap script that handles both:
   - a scaffold ZIP with no gitlink yet;
   - a normal clone whose submodule gitlink already exists.
4. Check out the exact recorded commit instead of following moving `master`.
5. Launch ComfyUI with `--base-directory <repo>/.comfy`.
6. Keep `.comfy/models`, input/output/temp/user state out of source control.
7. Do not place RetroModGen implementation files inside the ComfyUI submodule.
8. Document ComfyUI's separate upstream license and keep its upstream license/history intact.

### Tests

Offline:

- parse `config/comfyui.lock.json`;
- assert `.gitmodules` points to the expected repository/path;
- test bootstrap command construction with subprocess mocked if practical.

Live/source-control verification:

```bash
git submodule status
git -C third_party/ComfyUI rev-parse HEAD
```

The reported SHA must match the lock file.

### Verification

Start ComfyUI with `scripts/comfyui/run.py` and confirm it uses `.comfy` as its base directory. Creating output must not dirty the ComfyUI submodule.

### Acceptance criteria

- exact Comfy commit is reproducible;
- submodule is optional for core tests;
- runtime data does not pollute the submodule;
- updating Comfy requires an explicit gitlink + lock-file change.

### Expected tool calls

- GitHub/web: inspect the current upstream ComfyUI repository, release/commit, CLI flags, and license before changing the pin;
- shell/git: initialize/update/check the submodule and compare SHAs;
- local tests: verify config parsing and non-Comfy behavior.

### Starter prompt

```text
Implement RetroModGen UI1: pinned ComfyUI Git submodule and isolated runtime layout.

Inspect the repository first. Verify current ComfyUI upstream behavior from the official repository before changing any pin. Keep ComfyUI at third_party/ComfyUI and use --base-directory <repo>/.comfy so models, outputs, user state, and RetroModGen custom nodes do not modify the submodule. Implement/repair the bootstrap and launch helpers, lock file, ignore rules, and documentation.

Do not make ComfyUI a core Python dependency. Run core tests, verify the gitlink SHA matches the lock file when the submodule is available, launch ComfyUI if the environment supports it, and report exact commands/results.
```

## UI2 — Establish the `retromodgen_comfy` custom-node package and stable node contracts

### Objective

Expose RetroModGen capabilities in ComfyUI without duplicating compiler/business logic inside node classes.

### Likely files

```text
src/retromodgen_comfy/
.comfy/custom_nodes/retromodgen_comfy/__init__.py
tests/comfy/
docs/COMFYUI_INTEGRATION.md
```

### Implementation steps

1. Keep custom-node implementations in an importable `retromodgen_comfy` package.
2. Keep `.comfy/custom_nodes/retromodgen_comfy` as a tiny tracked loader that re-exports node mappings.
3. Define explicit custom socket types for structured values:
   - `RETROMODGEN_ASSET_SPEC`;
   - `RETROMODGEN_PROFILE`;
   - later mesh/rig/animation/report types.
4. Use normal Comfy scalar/image types where interoperability matters.
5. Require node classes to call public `retromodgen` core functions rather than reimplement stages.
6. Keep import-time behavior lightweight: no model loading and no ComfyUI import requirement for offline node-contract tests.
7. Give every node a stable class mapping name and human-readable display name.

### Tests

- import `retromodgen_comfy` without ComfyUI installed;
- assert `NODE_CLASS_MAPPINGS` and display mappings are valid;
- instantiate nodes directly and exercise pure-core paths;
- assert no node import triggers GPU/model loading.

### Verification

With Comfy running, query `/object_info` and verify the expected RetroModGen node names are registered.

### Acceptance criteria

- offline import works;
- Comfy discovery works;
- no compiler implementation is duplicated in node classes;
- node IDs are treated as compatibility-sensitive API names.

### Expected tool calls

- GitHub/web: inspect the exact pinned Comfy custom-node loading contract;
- repo search: inspect core functions before adding node wrappers;
- shell/pytest: run offline node contract tests;
- HTTP/live: query `/object_info` when Comfy is available.

### Starter prompt

```text
Implement RetroModGen UI2: the retromodgen_comfy custom-node package and stable node contracts.

Inspect existing core APIs and the pinned ComfyUI custom-node loader behavior first. Keep nodes as thin adapters and ensure importing/testing the node package does not require ComfyUI, CUDA, model weights, or GPU initialization. Add explicit custom socket types and stable NODE_CLASS_MAPPINGS.

Run focused node tests plus the full offline suite. If ComfyUI is available, verify the nodes appear in /object_info and in the node editor. Report exact commands/results.
```

## UI3 — Implement AssetSpec, profile, and validation nodes

### Objective

Provide the first useful ComfyUI-native RetroModGen graph that requires no GPU model: load/create an asset specification, resolve a retro profile, and validate it.

### Initial nodes

```text
RetroModGen_LoadAssetSpec
RetroModGen_CreateAssetSpec
RetroModGen_LoadProfile
RetroModGen_ValidateAssetSpec
RetroModGen_SaveAssetSpec
```

The scaffold already includes load-profile/load-spec/validate nodes; complete the family without breaking their stable mapping names.

### Implementation steps

1. Reuse Pydantic `AssetSpec` and core profile validation.
2. Add editor-friendly widgets for common spec fields while retaining an advanced JSON path.
3. Preserve schema version in serialized specs.
4. Return machine-readable validation reports plus a readable summary.
5. Ensure generated/saved spec paths are explicit and deterministic.
6. Add a minimal API-format workflow exercising these nodes.

### Tests

- valid profile/spec succeeds;
- invalid triangle/texture settings return the same issues as core validation;
- serialized round trip preserves rigging and animation fields;
- workflow template only references registered node IDs.

### Verification

Load `workflows/comfyui/spec_validate.api.json`/its UI equivalent, run it in Comfy, and verify the result matches `retromodgen validate` on the same file.

### Acceptance criteria

- Comfy and CLI validation agree;
- no duplicate validation implementation exists;
- a no-GPU live Comfy smoke graph works.

### Expected tool calls

- repo/file inspection;
- pytest;
- Comfy `/object_info` and `/prompt` integration when available;
- compare CLI and node output.

### Starter prompt

```text
Implement RetroModGen UI3: complete the AssetSpec/profile/validation ComfyUI node family.

Reuse the existing core Pydantic models and validators; do not duplicate rules in node code. Preserve the existing RetroModGen_LoadAssetSpec, RetroModGen_LoadProfile, and RetroModGen_ValidateAssetSpec mapping names. Add creation/save behavior and a versioned smoke workflow.

Test direct node calls without ComfyUI, compare results with the CLI validator, then run the workflow against the pinned ComfyUI instance if available. Report commands and evidence.
```

## UI4 — Add thin compiler, rigging, animation, and export node adapters

### Objective

Make the entire deterministic RetroModGen pipeline composable in the Comfy graph while keeping each node a wrapper around one core stage.

### Node groups

```text
Geometry:
  ImportMesh / NormalizeMesh / SimplifyMesh / QuantizeVertices / FreezeTopology / AnalyzeMesh

Texture:
  BakeTexture / DownscaleTexture / QuantizePalette / DitherTexture

Rigging/animation:
  AutoRig / GenerateSkinWeights / BuildIKControls / ValidateRig
  ImportAnimation / RetargetAnimation / BakeVertexFrames

Validation/export/preview:
  ValidateAsset / ExportGLB / ExportMD2 / ExportMDL / RenderTurntable
```

### Implementation steps

1. Only add a node after the corresponding core stage has a public API and tests.
2. Add structured Comfy socket types for mesh/rig/animation/report handles.
3. Prefer immutable/job-local artifact handles over huge Python objects crossing many nodes when that improves stability.
4. Keep topology freeze explicit in the graph. Rigging nodes must reject topology-changing input after bind unless the rig is intentionally invalidated.
5. Keep deform skeleton and authoring IK/control rig distinct.
6. Expose profile-driven defaults, but allow deliberate overrides that are later validated.
7. Export nodes must return file paths plus validation/provenance information.

### Tests

For every node:

- direct offline contract test using fixtures/mocks;
- equality/equivalence test against the underlying core function;
- failure-path test;
- no hidden dependency on a running Comfy server.

For rigging nodes add:

- skin weight normalization tests;
- topology hash mismatch rejection;
- IK control metadata preservation;
- GLB round-trip tests when E7 lands.

### Verification

Create a graph from fixture mesh -> normalize -> simplify -> validate -> GLB export. Later extend it through freeze -> rig -> weights -> IK -> animation -> rigged GLB and optional MD2/MDL bake. Compare outputs against CLI orchestration using the same `AssetSpec`.

### Acceptance criteria

- graph and CLI call the same core logic;
- no stage has two independent implementations;
- deterministic fixture outputs/metrics agree within documented tolerances;
- rigging remains skeletal/canonical until explicit legacy export bake.

### Expected tool calls

- repo search for core APIs;
- pytest/fixture tools;
- Comfy live graph verification;
- GLB/MDL/MD2 validators and independent viewers when applicable.

### Starter prompt

```text
Implement the next RetroModGen UI4 node adapter for an already-implemented core stage.

Before coding, identify the public core function and its tests. The Comfy node must be a thin adapter only: translate inputs, call core, return structured outputs/diagnostics. Do not duplicate algorithms or profile rules. Preserve topology/rig invariants when the node touches articulated assets.

Add direct offline node tests and equivalence tests against the core function, run the full suite, and if ComfyUI is available exercise the node in a minimal graph. Report exact evidence.
```

## UI5 — Build versioned ComfyUI workflows and editor UX

### Objective

Turn the node collection into practical reusable authoring graphs for source generation, static retro compilation, and rigged character creation.

### Required workflow templates

```text
spec_validate.api.json
hunyuan_source_mesh.api.json
trellis_source_mesh.api.json
retro_static_prop.api.json
retro_character_rigged_glb.api.json
retro_character_dual_export.api.json
```

### Implementation steps

1. Separate API-format and UI-format workflow files by naming convention.
2. Never commit absolute user paths, secrets, or model weights.
3. Create reusable subgraphs/groups where current Comfy supports them cleanly.
4. Expose a small number of art-directable controls at the graph surface:
   - target profile;
   - triangle budget;
   - texture size/palette/dither;
   - seed/candidate count;
   - rigging on/off/backend;
   - IK/control rig on/off;
   - export targets.
5. Hide low-level implementation noise in reusable subgraphs once stable.
6. Add workflow metadata documenting required external custom nodes/model checkpoints.
7. Add one static and one skeletal reference workflow screenshot only after the UI is stable; screenshots are documentation, not test evidence.

### Tests

- parse every committed workflow JSON;
- assert required RetroModGen node IDs exist;
- validate placeholders/config keys;
- smoke-submit non-GPU workflows in live Comfy;
- model workflows become opt-in live tests.

### Verification

A user should be able to open a documented workflow, change the target profile/triangle budget, run it, and receive validated outputs without editing Python.

### Acceptance criteria

- workflows are versioned and reproducible;
- required third-party nodes/models are documented;
- static and rigged-character paths are represented;
- workflow output includes provenance sufficient to reconstruct the run.

### Expected tool calls

- GitHub/web for current Comfy workflow/subgraph behavior and upstream model-node changes;
- JSON/file validation;
- live Comfy submission;
- output validation/render inspection.

### Starter prompt

```text
Implement RetroModGen UI5: versioned ComfyUI workflow templates and editor UX.

Inspect the pinned ComfyUI version and currently available RetroModGen nodes first. Build/update the next workflow using stable node IDs and no machine-specific paths. Record required model/custom-node dependencies and expose only meaningful art-direction controls.

Parse/test the workflow offline, submit any non-GPU workflow to the pinned Comfy instance when available, and for GPU workflows capture the exact backend/model identifiers and validated outputs.
```

## UI6 — ComfyUI compatibility, upgrade, and integration-test harness

### Objective

Make ComfyUI upgrades deliberate and detectable instead of allowing upstream node/API churn to silently break RetroModGen.

### Implementation steps

1. Add an opt-in `comfy_live` pytest marker.
2. Add a live smoke test that checks `/system_stats` and `/object_info`.
3. Verify required RetroModGen nodes are present.
4. Once B1 lands, submit the no-GPU spec-validation workflow through `/prompt` and verify completion/history.
5. Add mocked contract tests for every API payload consumed by `ComfyUIBackend`.
6. Record the Comfy commit in job provenance.
7. Create an upgrade checklist: inspect upstream changes -> update gitlink/lock -> offline tests -> live node discovery -> API workflow -> representative GPU workflow -> commit.
8. Never update the Comfy submodule pin as an unrelated side effect.

### Tests

Default CI:

```bash
pytest -m "not comfy_live"
```

Opt-in live:

```bash
RETROMODGEN_COMFY_LIVE=1 pytest -m comfy_live
python scripts/comfyui/verify.py
```

### Verification

Intentionally point the live test at a server without RetroModGen nodes and verify it fails with an actionable missing-node report. Then run against the pinned configured server and verify success.

### Acceptance criteria

- ordinary CI remains GPU/Comfy-free;
- live compatibility test clearly identifies missing/broken node contracts;
- Comfy upgrades are tied to explicit lock/gitlink changes and test evidence.

### Expected tool calls

- GitHub/web: inspect upstream changes before pin updates;
- git/submodule commands;
- pytest;
- HTTP `/system_stats`, `/object_info`, `/prompt`, `/history`;
- representative generation workflow after inference-node changes.

### Starter prompt

```text
Implement RetroModGen UI6: ComfyUI compatibility and upgrade test harness.

Keep default CI completely Comfy/GPU-free. Add mocked API-contract coverage and an opt-in live suite that checks server health, required RetroModGen node discovery, and a no-GPU workflow submission once the API client exists. Tie every live result to the exact ComfyUI git commit from the submodule.

Do not advance the Comfy pin unless specifically requested. Run focused tests, full offline tests, and live tests only when the environment is available; report all commands/results.
```

---

# Phase B — First real static asset

## B1 — ComfyUI HTTP/WebSocket client adapter

### Objective

Connect RetroModGen to an externally running ComfyUI instance without importing ComfyUI into the RetroModGen process.

### Likely files

```text
src/retromodgen/backends/comfyui.py
src/retromodgen/backends/comfy_client.py
tests/test_comfy_client.py
.env.example
docs/BACKENDS.md
```

### Implementation steps

1. Verify the current ComfyUI API using upstream documentation/source.
2. Implement health/availability probing.
3. Submit a workflow JSON.
4. Track the returned prompt/job identifier.
5. Wait/poll/listen for completion with timeout.
6. Download or locate output artifacts.
7. Normalize the result into `GeneratedAsset`.
8. Add clear errors for:
   - connection refused;
   - timeout;
   - workflow rejection;
   - missing output;
   - malformed response.
9. Make server URL configurable.
10. Do not hardcode Hunyuan-specific nodes in the generic client.

### Automated tests

Mock the Comfy HTTP/WebSocket API and test:

- submit success;
- queue/completion handling;
- timeout;
- server unavailable;
- malformed response;
- result file resolution.

### Integration test

With ComfyUI running:

```bash
retromodgen backends
retromodgen comfy health
```

or equivalent backend probe command.

### Verification

Shut ComfyUI down and confirm the rest of the CLI still works.

### Acceptance criteria

Core package remains fully usable when `127.0.0.1:8188` is absent.

### Expected tool calls

- web/GitHub to inspect current official ComfyUI API behavior;
- repository edits;
- mocked local HTTP tests;
- optional live integration test when ComfyUI exists.

### Starter prompt

```text
Implement RetroModGen action item B1: ComfyUI external-service client.

First inspect the existing backend contract. Then verify the current ComfyUI server API from official ComfyUI documentation/source before writing integration code. RetroModGen must communicate over HTTP/WebSocket; do not import or vendor ComfyUI.

Implement availability checks, workflow submission, completion tracking, output retrieval, timeout handling, and normalized GeneratedAsset results. Add fully mocked tests so CI does not need ComfyUI. If a local ComfyUI instance is available, run the live health integration test; otherwise clearly mark that live test as not run while still completing all mocks and core tests.
```

---

## B2 — First real image-to-3D workflow adapter

### Objective

Support one real source-generation workflow end-to-end, initially Hunyuan3D or another selected backend available through ComfyUI.

### Scope

Do not attempt to support every model. Prove one workflow first.

### Likely files

```text
workflows/
  hunyuan_image_to_shape.json
src/retromodgen/backends/workflows/*.py
tests/workflows/
docs/BACKENDS.md
```

### Implementation steps

1. Check current ComfyUI support for the selected model.
2. Create a minimal image-to-3D workflow.
3. Identify which workflow inputs RetroModGen is allowed to patch:
   - source image;
   - seed;
   - steps/quality preset if needed;
   - output name.
4. Keep workflow node IDs encapsulated in one adapter.
5. Store a workflow version identifier in job metadata.
6. Return GLB/OBJ or the model’s native mesh output as a source asset.
7. Add a model/backend capability description.

### Tests

- workflow JSON parses;
- expected patch points exist;
- seed/input substitution is deterministic;
- malformed/outdated workflow gives useful error;
- mocked Comfy result maps correctly to `GeneratedAsset`.

### Live verification

Use a simple reference image such as an isolated crate.

```bash
retromodgen generate examples/quake2_crate.asset.json \
  --backend comfyui \
  --output build/comfy-crate
```

Verify a source mesh is produced before retro compilation.

### Acceptance criteria

A single documented Comfy workflow can generate a source mesh through RetroModGen without manually interacting with the ComfyUI node editor.

### Expected tool calls

- official GitHub/web research for current workflow/model nodes;
- Comfy live service if available;
- shell/file inspection;
- mocked tests regardless of live availability.

### Starter prompt

```text
Implement RetroModGen action item B2: first real ComfyUI image-to-3D workflow adapter.

Use current official ComfyUI/model information to select and verify one supported image-to-3D path, preferably Hunyuan3D if it remains practical. Do not generalize to every model yet. Add one versioned workflow and a small adapter that patches only explicit inputs such as source image, seed, and output naming.

Add offline tests for workflow integrity and input patching. If ComfyUI/model weights are available, run one live isolated-crate generation and record the exact command/output. If not, leave the live test instructions documented but finish all dependency-independent work.
```

---

## B3 — Mesh import normalization and sanitation

### Objective

Convert arbitrary source meshes into a predictable internal representation before simplification.

### Required normalization

At minimum handle:

- scene vs mesh containers;
- transforms;
- coordinate system/up-axis normalization;
- unit normalization policy;
- triangulation;
- normals;
- finite position checks;
- degenerate triangle removal;
- disconnected tiny components according to configurable threshold;
- material/texture reference collection;
- bounding box and basic metrics.

### Likely files

```text
src/retromodgen/mesh/io.py
src/retromodgen/mesh/normalize.py
src/retromodgen/mesh/metrics.py
tests/test_mesh_normalization.py
tests/assets/
```

### Tests

Create fixtures for:

- transformed scene;
- quad mesh requiring triangulation;
- degenerate triangles;
- NaN/Inf rejection;
- tiny disconnected component;
- already valid mesh.

### Verification

```bash
retromodgen inspect tests/assets/<fixture>.glb --json
```

Verify stable metrics:

```text
vertex_count
triangle_count
bounds
surface_area
component_count
material_count
```

### Acceptance criteria

Downstream compiler stages can assume a documented normalized mesh contract.

### Expected tool calls

- shell and unit tests;
- upstream trimesh/PyMeshLab documentation only if API details are uncertain.

### Starter prompt

```text
Implement RetroModGen action item B3: mesh import normalization and sanitation.

Inspect existing compiler interfaces and profile constraints. Add a normalized mesh boundary that handles scene transforms, triangulation, finite positions, normals, degenerates, small disconnected components, bounds, and source material references. Keep the internal contract explicit and testable.

Build small deterministic mesh fixtures covering malformed and transformed inputs. Add inspectable metrics and run focused/full tests. Avoid adding the custom QEM simplifier here; this step is only normalization/sanitation.
```

---

## B4 — Baseline existing-library mesh simplification

### Objective

Reach the first working low-poly result using a mature existing simplification library before implementing custom weighted QEM.

### Implementation steps

1. Evaluate already-installed/planned mesh library support.
2. Select one baseline simplifier.
3. Simplify toward `target_triangles`.
4. Enforce `hard_max_triangles`.
5. Preserve UV/material data when feasible.
6. Record before/after metrics.
7. Clearly label this implementation as baseline/reference.

### Tests

- exact/near target on fixture meshes;
- hard maximum never exceeded;
- empty/too-small meshes fail cleanly;
- deterministic output metrics;
- source mesh is not modified in place unexpectedly.

### Visual verification

Generate before/after turntable or static comparison for at least one asymmetric fixture.

### Acceptance criteria

The Phase B pipeline can turn an oversized source mesh into a legal `quake2_prop` mesh even though the result is not yet the final quality target.

### Expected tool calls

- local library investigation;
- web docs if simplifier API/version behavior is uncertain;
- tests and mesh inspection.

### Starter prompt

```text
Implement RetroModGen action item B4: baseline existing-library simplification.

Do not implement custom QEM yet. Use a mature available mesh library to provide a reference simplifier that reduces normalized meshes toward AssetSpec target_triangles and never exceeds hard_max_triangles. Record before/after metrics and preserve UV/material data when practical.

Add deterministic tests and one visual/fixture comparison. Document limitations because this implementation will later serve as the baseline against the custom weighted simplifier.
```

---

## B5 — Retro texture compiler v1

### Objective

Compile modern/high-resolution source textures into intentionally low-resolution retro textures.

### Required v1 capabilities

- bake or transfer source appearance onto final UVs where needed;
- resize to target dimensions;
- nearest-neighbor output intent;
- palette abstraction;
- RGB quantization;
- optional indexed-color output;
- ordered Bayer dithering;
- optional Floyd-Steinberg or similar error diffusion;
- configurable contrast/detail shaping;
- deterministic seed where any stochastic processing is used.

### Likely files

```text
src/retromodgen/texture/
  compiler.py
  palette.py
  dither.py
  resize.py
  metrics.py
tests/test_texture_*.py
tests/assets/textures/
```

### Tests

Golden-image or metric-based tests for:

- target dimensions;
- palette membership;
- deterministic dithering;
- alpha behavior;
- no unintended smoothing;
- known small synthetic patterns.

Avoid fragile pixel-exact tests for operations that legitimately differ by library version unless the algorithm is fully owned by the project.

### Verification

Produce 64x64, 128x128, and 256x256 outputs from the same source and inspect them at **native resolution**, not only zoomed/smoothed.

### Acceptance criteria

The resulting texture looks intentionally authored for a low-resolution asset rather than merely being a blurry downsample.

### Expected tool calls

- image/file inspection;
- test execution;
- web only for format/library behavior that needs confirmation.

### Starter prompt

```text
Implement RetroModGen action item B5: retro texture compiler v1.

Build deterministic low-resolution texture processing independent of ComfyUI. Support target sizing, palette abstraction/quantization, nearest-neighbor presentation intent, ordered dithering, and one error-diffusion option. Use synthetic test images so behavior can be verified automatically.

Do not add Quake copyrighted palette data directly unless licensing/source rules are satisfied; design the loader so a palette can be supplied externally. Generate native-resolution verification outputs and run the full test suite.
```

---

## B6 — GLB export, validation report, and deterministic preview

### Objective

Finish the first complete static-prop pipeline.

### Deliverables

- final GLB writer;
- final asset manifest;
- profile validation report;
- deterministic preview/turntable path;
- human-readable summary.

### Implementation steps

1. Export normalized compiled geometry and target textures to GLB.
2. Store provenance in sidecar `manifest.json` rather than relying only on custom GLB extensions.
3. Add generic mesh/profile validation.
4. Add preview rendering using the simplest available path.
5. Prefer a renderer that does not require ComfyUI.
6. If Blender is used, invoke it externally and make it optional.
7. Render with nearest-neighbor texture sampling and retro-appropriate simple lighting where possible.

### Acceptance test

Given a fixture or real generated industrial crate:

```bash
retromodgen compile source.glb \
  --profile quake2_prop \
  --output build/quake2-crate
```

Expected output:

```text
build/quake2-crate/
  asset.glb
  manifest.json
  validation.json
  textures/...
  preview/...
```

### Verification

- GLB reopens successfully;
- triangle budget passes;
- texture dimensions pass;
- all referenced files exist;
- preview can be inspected;
- compile command returns zero.

### Acceptance criteria

This completes the first vertical slice: source mesh -> retro GLB with no ComfyUI requirement during compilation.

### Expected tool calls

- shell/CLI;
- GLB re-import;
- optional Blender invocation;
- tests.

### Starter prompt

```text
Implement RetroModGen action item B6: final GLB export, validation report, and deterministic preview for the static-prop vertical slice.

Use the normalized/simplified mesh and retro texture outputs already in the repository. Export a re-loadable GLB, create manifest.json and validation.json, and provide a deterministic preview path that remains optional if Blender is unavailable. The compilation path itself must not depend on ComfyUI.

Run an end-to-end compile of a fixture/source asset, re-import the GLB, verify all profile constraints, and run the full tests. Include exact output paths and metrics in the completion summary.
```

---

# Phase C — Purpose-built retro geometry compiler

## C1 — Scalar weighted-QEM reference simplifier

### Objective

Implement a project-owned, deterministic reference version of quadric error metric edge-collapse simplification.

### Rule

Correctness and inspectability matter more than speed in this task.

### Initial cost

Start with:

```text
cost = geometric_quadric_error
```

Then expose hooks for later weights.

### Implementation steps

1. Define internal mesh adjacency representation.
2. Build per-face/per-vertex quadrics.
3. Enumerate valid collapse candidates.
4. Compute optimal/fallback collapse positions.
5. Maintain a priority queue.
6. Reject topology-invalid collapses.
7. Repeat until target count or no legal collapse remains.
8. Make tie breaking deterministic.
9. Record collapse/error metrics.

### Tests

Use mathematically simple meshes:

- plane/grid;
- cube;
- subdivided cube;
- asymmetric low-poly shape;
- disconnected mesh;
- boundary-heavy mesh.

Validate:

- no invalid indices;
- no NaN/Inf;
- target triangle behavior;
- deterministic topology/metrics;
- no new degenerate triangles above tolerance.

### Baseline comparison

Compare against B4 at equal triangle counts. At this stage only verify that geometry error is sane; quality weighting comes later.

### Acceptance criteria

A readable scalar/reference QEM implementation is covered by regression tests.

### Expected tool calls

- repository code inspection;
- algorithm references if needed;
- Python/C++ test execution depending on chosen reference language;
- no premature SIMD.

### Starter prompt

```text
Implement RetroModGen action item C1: scalar deterministic weighted-QEM foundation.

Start by reading the current normalization and baseline simplifier code. Implement the simplest correct project-owned QEM edge-collapse reference algorithm with geometric quadric error only, deterministic tie breaking, topology-safety checks, and metrics. Do not add silhouette/semantic weighting yet and do not optimize with SIMD.

Add regression fixtures for grids, cubes, boundaries, and asymmetric meshes. Compare metrics with the existing-library baseline at equal triangle counts. Run focused tests, full tests, and show deterministic repeated-run evidence.
```

---

## C2 — Silhouette, hard-edge, boundary, and UV-seam preservation

### Objective

Make simplification produce deliberately useful low-poly game geometry rather than generic decimation.

### Proposed cost model

```text
cost =
    geometric_error
  + Wsilhouette * silhouette_penalty
  + Wsharp      * hard_edge_penalty
  + Wboundary   * boundary_penalty
  + Wuv         * uv_seam_penalty
```

### Implementation steps

1. Identify boundary edges.
2. Identify hard/feature edges using configurable dihedral angle.
3. Identify UV seams.
4. Define a view-independent silhouette proxy first.
5. Add weights to the profile/compiler config.
6. Keep all weights zeroable for baseline comparison.
7. Record per-component error contribution for diagnostics.

### Tests

Construct fixtures where ordinary QEM predictably damages:

- box corners;
- thin weapon-like extension;
- UV seam;
- sharp ridge;
- boundary loop.

Verify weighted mode preserves marked features better at the same triangle budget.

### Acceptance criteria

There is measurable improvement over plain QEM in purpose-built fixtures, not merely subjective visual claims.

### Expected tool calls

- local tests/metrics;
- algorithm research when needed;
- preview comparison generation.

### Starter prompt

```text
Implement RetroModGen action item C2: silhouette, hard-edge, boundary, and UV-seam weighting for the QEM simplifier.

Build on C1 rather than rewriting it. Add independent, configurable penalty terms for boundaries, sharp feature edges, UV seams, and a practical view-independent silhouette proxy. All weights must be disableable so plain-QEM comparisons remain possible.

Create adversarial fixtures where unweighted QEM destroys important features and add measurable before/after assertions at identical triangle budgets. Generate visual comparison artifacts when possible and run all tests.
```

---

## C3 — Semantic importance masks

### Objective

Allow important regions such as face, hands, weapon, or signature silhouette details to retain more geometry.

### Data model

Support semantic weights independently of how they were produced.

Possible representation:

```text
per-vertex weight
per-face weight
named semantic region -> weight
```

### Implementation steps

1. Add semantic weight data to the compiler input contract.
2. Add import path for masks/weights.
3. Integrate semantic penalty into collapse cost.
4. Define sensible normalization/clamping.
5. Keep semantic weighting optional.
6. Expose diagnostic heatmap/data output.

### Tests

Create a fixture with two identical protrusions where one is marked important. At severe decimation, the important region should retain measurably more shape fidelity.

### Acceptance criteria

The simplifier is agnostic to whether semantic data came from a human, image segmentation model, or LLM/vision stage.

### Expected tool calls

- no external AI service required;
- mesh tests and metrics;
- optional visualization.

### Starter prompt

```text
Implement RetroModGen action item C3: semantic importance masks for geometry simplification.

Do not couple this feature to an LLM or segmentation model. Extend the compiler contract to accept optional per-face/per-vertex semantic importance and integrate it as another configurable collapse penalty. Add a deterministic fixture proving a marked feature survives aggressive simplification better than an equivalent unmarked feature.

Expose enough diagnostic data to inspect the applied weights, then run focused/full tests.
```

---

## C4 — Native C++ simplifier and Python binding

### Objective

Move the proven simplifier hot path to C++ only after C1-C3 are stable.

### Implementation steps

1. Freeze reference behavior and fixtures first.
2. Define a narrow C ABI or pybind11/nanobind-style boundary.
3. Keep Python orchestration/data validation outside the native module.
4. Port the algorithm with equivalent deterministic behavior where practical.
5. Add benchmark harness.
6. Compare result metrics against reference implementation.
7. Keep Python fallback initially.

### Build verification

Windows/MSVC:

```bash
cmake -S native -B native/build
cmake --build native/build --config Release
```

Also test the selected Python binding build/install path.

### Tests

- reference/native parity on fixture corpus;
- no crashes on malformed-but-rejected inputs;
- repeated-run determinism;
- benchmark output recorded but no arbitrary speed target yet.

### Acceptance criteria

Native implementation passes the same semantic/feature preservation regression suite as the reference implementation.

### Expected tool calls

- CMake/compiler shell calls;
- tests;
- profiler only if necessary;
- no algorithmic redesign during port.

### Starter prompt

```text
Implement RetroModGen action item C4: native C++ version of the proven weighted-QEM simplifier.

Before coding, inspect the complete reference implementation and regression corpus. Port behavior rather than redesigning it. Keep a narrow Python/native boundary, preserve a Python fallback, and add parity tests comparing target counts, validity, feature metrics, and error metrics across the fixture corpus.

Build with CMake in Release mode, run native/reference parity tests and the complete suite, and include a small benchmark report without sacrificing correctness for speed.
```

---

# Phase D — Quake-family native formats

## D1 — Quake II MD2 reader/writer and validator

### Objective

Support true Quake II-style vertex-frame model export.

### Implementation steps

1. Verify MD2 format definitions from authoritative source/reference implementations.
2. Implement reader first for known-good corpus inspection.
3. Implement in-memory model representation.
4. Implement writer.
5. Enforce format hard limits.
6. Implement position quantization and quantization-error reporting.
7. Implement UV/skin coordinate handling.
8. Implement frame naming/ranges.
9. Add round-trip tests.

### Testing

- parse known-good MD2 fixture;
- write -> read round trip;
- invalid header/version rejection;
- limit overflow rejection;
- frame topology consistency;
- quantization bounds;
- viewer/engine smoke test when available.

### Verification

Open exported model in at least one independent MD2 viewer/engine/tool and document the result.

### Acceptance criteria

RetroModGen can export a legal MD2 from a fixed-topology mesh/animation source and can explain any precision loss.

### Expected tool calls

- web/GitHub authoritative format/source lookup;
- binary fixture inspection;
- unit/roundtrip tests;
- external viewer smoke test if available.

### Starter prompt

```text
Implement RetroModGen action item D1: Quake II MD2 reader/writer/validator.

First verify the format using authoritative Quake II source or well-established format documentation. Implement a reader before or alongside the writer so round-trip testing is possible. Enforce all hard limits explicitly and report vertex position quantization error rather than hiding it.

Add known-good/known-bad binary fixtures where licensing permits, round-trip tests, and one independent viewer/engine smoke-test procedure. Run the complete suite and document every format assumption.
```

---

## D2 — Quake 1 MDL reader/writer and validator

### Objective

Support Quake 1 alias model output as a separate exporter rather than pretending MDL and MD2 are the same format.

### Implementation steps

1. Verify MDL v6 layout and limits.
2. Implement parser/validator.
3. Implement skin/palette handling through a supplied palette source.
4. Implement vertex-frame handling.
5. Implement writer and round-trip tests.
6. Enforce target-engine hard limits.

### Tests/verification

Same philosophy as D1:

- known-good parsing;
- malformed rejection;
- round-trip;
- engine/viewer smoke test;
- palette/index validation;
- frame topology validation.

### Acceptance criteria

MDL and MD2 code share only genuinely common utilities; format-specific logic remains format-specific.

### Expected tool calls

- authoritative Quake source/web research;
- binary tests;
- viewer smoke test.

### Starter prompt

```text
Implement RetroModGen action item D2: Quake 1 MDL v6 reader/writer/validator.

Verify the binary layout and limits from authoritative Quake source/reference material before coding. Keep MDL-specific skin/indexed-palette and frame behavior separate from MD2. Do not bundle copyrighted palette files into the project unless clearly permitted; allow users to supply a palette file.

Add round-trip, malformed-input, hard-limit, palette, and frame-topology tests, plus an independent viewer/engine verification procedure. Run all tests and document assumptions.
```

---

# Phase E — Character, skeletal rigging, IK, and animation support

Phase E establishes skeletal animation as RetroModGen's **canonical character representation**. MDL/MD2 vertex frames are compatibility exports produced from the skeletal source.

All generated characters, creatures, and articulated models should leave this phase with:

```text
frozen low-poly mesh
+ deform skeleton
+ bind pose
+ normalized skin weights
+ semantic bone-role map where possible
+ optional IK/control rig
+ rig-validation report
```

Static props remain exempt unless their profile/request enables articulation.

## E1 — Rigging data model and topology-freeze contract

### Objective

Define the point after which topology is frozen and establish a model-agnostic skeletal/skin contract that every rigging backend must produce.

### Proposed data model

Add a `RigSpec` to `AssetSpec` or the compiled character specification with a deliberately small v1 surface:

```text
rigging.enabled
rigging.mode                  none | auto | template | imported
rigging.archetype             auto | humanoid | quadruped | creature | mechanical
rigging.rest_pose             source | a_pose | t_pose
rigging.generate_ik           bool
rigging.max_bones             optional profile limit
rigging.max_influences        default 4 unless profile overrides
rigging.backend               auto | tokenrig | unirig | blender_template | ...
```

Define backend-independent runtime structures for:

```text
Skeleton
  Bone[]
    name
    parent_index
    local_rest_transform
    semantic_role?        # hips, spine, head, upper_arm.L, etc.

SkinBinding
  joints_per_vertex
  weights_per_vertex
  inverse_bind_matrices

RiggedAsset
  frozen_mesh
  skeleton
  skin_binding
  animation_clips[]
  rig_report
```

Keep control-rig/IK metadata separate from the deform skeleton contract.

### Implementation steps

1. Add character/articulated-asset compiler state.
2. Freeze topology after final low-poly geometry and UV compilation.
3. Add `RigSpec` validation and defaults by profile.
4. Define backend-independent `Skeleton`, `Bone`, `SkinBinding`, `RiggedAsset`, and rig-report structures.
5. Define semantic bone-role naming independent of any one auto-rigger.
6. Add explicit invalidation semantics: a topology-changing operation after binding must fail unless the rig is discarded and regenerated.
7. Define skeleton coordinate/basis conventions and unit scale in one place.
8. Extend provenance so the rigging backend/model/version/config are recorded.

### Tests

- topology-freeze violation;
- valid and cyclic/invalid bone hierarchies;
- multiple-root policy;
- parent-index validation;
- bind-matrix count validation;
- valid/invalid skin joint indices;
- skin weight normalization tolerance;
- max influences per vertex;
- `rigging.mode=none` remains valid for static props;
- deterministic serialization of a small rig fixture.

### Verification

Create a tiny synthetic two-bone skinned strip/cylinder fixture and serialize/reload the internal rig representation. Confirm that the mesh vertex/index count and rest-pose deformation are unchanged.

### Acceptance criteria

RetroModGen can answer all of the following without Blender or a GPU:

```text
Is the asset expected to be rigged?
Is topology frozen?
Is the skeleton hierarchy valid?
Are all skin weights and joint references valid?
Which bones correspond to semantic roles?
Which rigging backend produced this asset?
```

### Expected tool calls

- repository/schema inspection;
- Khronos glTF specification lookup when defining interchange semantics;
- local fixture generation and pytest;
- no GPU or live rigging model required.

### Starter prompt

```text
Implement RetroModGen action item E1: rigging data model and topology-freeze contract.

Treat bone-based skeletal animation as the canonical representation for generated characters, creatures, and articulated assets. Inspect the current AssetSpec, pipeline, compiler, and exporter interfaces first. Add a small RigSpec plus backend-independent Skeleton/Bone/SkinBinding/RiggedAsset structures. Freeze topology after final low-poly geometry/UV compile and reject topology-changing stages after skin binding unless the rig is explicitly invalidated.

Define deterministic coordinate/unit conventions, semantic bone roles, hierarchy validation, joint/weight validation, and provenance fields. Add a tiny two-bone fixture and comprehensive offline tests. Consult the current Khronos glTF skinning specification for interchange semantics. Run focused tests and the complete suite and report exact commands/results.
```

---

## E2 — Rigging backend abstraction and backend evaluation spike

### Objective

Make automatic rigging replaceable in the same way geometry generation is replaceable, then evaluate at least one generic learned auto-rigger and one deterministic/template fallback.

### Interface

```python
class RiggingBackend:
    def rig(
        self,
        mesh: FrozenMesh,
        spec: RigSpec,
        output_dir: Path,
    ) -> RiggingResult:
        ...
```

The backend returns the E1 canonical rig representation or an interchange asset that can be normalized into it.

### Candidates to evaluate

At implementation time, verify current upstream status/licenses/hardware requirements rather than relying on this document's snapshot.

1. **TokenRig / SkinTokens** — current learned candidate capable of predicting a skeleton hierarchy and dense skin weights from a mesh.
2. **UniRig** — useful alternative/reference implementation for automatic skeleton and skin prediction.
3. **Blender template/armature path** — deterministic fallback for known archetypes such as humanoids; skeleton placement may be template/landmark driven, followed by automatic or explicit weights.
4. Manual/imported rig — must remain supported even if automatic rigging fails.

As of the planning update, TokenRig's public repository describes direct mesh -> skeleton + skin generation and an optional path that skins an existing skeleton. Treat this as a candidate, not a permanent architectural dependency.

### Implementation steps

1. Add a lazy rigging-backend registry separate from geometry backends.
2. Implement `MockRiggingBackend` for CI.
3. Define capability reporting:
   - skeleton generation;
   - skin generation;
   - supported archetypes;
   - existing-skeleton skinning;
   - GPU requirement;
   - control-rig generation, if any.
4. Build a small evaluation harness that runs the same frozen meshes through candidate backends.
5. Normalize all backend results into E1 structures.
6. Record backend/model/version/config and execution metrics.
7. Fail gracefully when a GPU/model backend is unavailable.
8. Do not let learned-rigging dependencies leak into core imports.

### Tests

- registry lookup and lazy import;
- mock backend deterministic result;
- unavailable optional backend diagnostic;
- normalization from backend result into E1 structures;
- capability filtering;
- static `rigging.mode=none` bypass.

### Verification

Use at least these evaluation meshes when live backends are available:

```text
humanoid
quadruped
non-humanoid creature
simple articulated robot
```

Produce a comparison report containing skeleton validity, bone count, skin-weight validity, pose-test metrics, runtime, and VRAM if measurable.

### Acceptance criteria

RetroModGen does not care which auto-rigger produced the rig after normalization, and CI can exercise the contract using `MockRiggingBackend` without a GPU.

### Expected tool calls

- current GitHub/web review of TokenRig/SkinTokens, UniRig, and Blender documentation;
- local tests;
- optional GPU shell execution for live backend trials;
- artifact inspection in Blender for live comparison runs.

### Starter prompt

```text
Implement RetroModGen action item E2: rigging backend abstraction and evaluation harness.

Inspect E1 and the existing geometry-backend registry before coding. Add a separate lazy RiggingBackend registry plus a deterministic MockRiggingBackend. The core must not import TokenRig, UniRig, PyTorch, CUDA, or Blender merely to list or validate rigs.

Then perform a current-source research spike on VAST-AI-Research/SkinTokens (TokenRig), VAST-AI-Research/UniRig, and Blender's armature/automatic-weight path. Document current licenses, runtime requirements, supported inputs/outputs, and integration risks without hard-coding a permanent winner. Add capability reporting and a live comparison harness that is optional in CI. Run focused/full offline tests; run live tests only if dependencies are available and clearly state what was or was not executed.
```

---

## E3 — Automatic skeleton generation and semantic bone mapping

### Objective

Generate or import a valid deform skeleton for the frozen low-poly mesh and normalize it to RetroModGen's semantic bone-role system.

### Implementation steps

1. Accept skeletons from an automatic rigging backend, template generator, or imported rig.
2. Validate hierarchy:
   - acyclic;
   - valid parent references;
   - supported root policy;
   - finite transforms;
   - nonzero/valid bone lengths where applicable.
3. Normalize coordinate system, scale, rest pose, and bone transforms.
4. Map backend-specific bone names to semantic roles where possible:
   - root/hips;
   - spine/chest/neck/head;
   - upper/lower arm and hand;
   - upper/lower leg and foot;
   - optional tail/wing/jaw/etc.
5. Preserve unmapped bones rather than deleting them.
6. Add optional archetype-specific required-role checks.
7. Generate a skeleton visualization artifact for QA.
8. Record confidence/source for semantic mappings when produced heuristically.

### Tests

Use synthetic rigs to verify:

- hierarchy validation;
- cycle detection;
- coordinate conversion;
- left/right mapping;
- duplicate/missing names;
- unknown bones preserved;
- required-role validation for a humanoid fixture;
- arbitrary creature rig can remain valid without humanoid roles.

### Verification

For at least one generated humanoid and one non-humanoid mesh, render the skeleton overlaid on the mesh in rest pose and verify joint locations are plausible before skinning is accepted.

### Acceptance criteria

Downstream IK, retargeting, validation, and export code consume normalized semantic roles instead of backend-specific bone names.

### Expected tool calls

- local hierarchy/math tests;
- Blender headless visualization or equivalent;
- live rigging backend only for integration verification;
- web lookup if backend output conventions are unclear.

### Starter prompt

```text
Implement RetroModGen action item E3: automatic skeleton normalization and semantic bone mapping.

Use the E1 canonical skeleton contract and E2 backend interface. Normalize skeletons from mock/imported/automatic sources into one coordinate and rest-pose convention, validate hierarchy rigorously, and map backend-specific names to semantic roles without requiring a humanoid skeleton for arbitrary creatures.

Add synthetic hierarchy fixtures for cycles, left/right mapping, coordinate conversion, unknown bones, and required-role checks. Produce an optional skeleton-overlay QA artifact. Run all offline tests, and if a live auto-rigger is available, verify one humanoid and one non-humanoid result.
```

---

## E4 — Skin-weight generation, cleanup, and deformation QA

### Objective

Bind the frozen low-poly mesh to the deform skeleton with stable skin weights suitable for low-poly animation.

### Important retro-specific requirement

Low-poly meshes can deform badly when generic smooth weights spread across very few vertices. RetroModGen should prefer **simple, localized, inspectable weighting** over unnecessarily smooth modern deformation.

### Implementation steps

1. Accept weights from an auto-rigger or generate them from an existing skeleton.
2. Normalize weights per vertex.
3. Enforce configurable `max_influences`.
4. Remove tiny influences below a threshold and renormalize.
5. Detect weights referencing missing joints.
6. Detect disconnected-part weight bleeding.
7. Add optional hard/rigid weighting mode for mechanical parts.
8. Add optional low-poly weight sharpening to favor dominant bones.
9. Generate bind matrices.
10. Implement a pose-sweep QA suite using semantic joints when available.
11. Produce deformation metrics and optional rendered contact sheet.

### Pose-sweep examples

```text
shoulder flexion/abduction
elbow 0 -> configured bend
hip flexion
knee bend
head turn
jaw/tail/wing test when roles exist
mechanical hinge rotation
```

### Tests

- all weights finite and nonnegative;
- weight sums approximately one for bound vertices;
- influences <= profile maximum;
- deleted influences correctly renormalize;
- rigid part remains rigid;
- two-bone analytic fixture has numerically known deformation;
- disconnected island does not receive impossible remote influences in the cleanup fixture;
- inverse bind matrices reconstruct rest pose within tolerance.

### Verification

Run deformation QA on a low-poly humanoid fixture and inspect extreme poses for elbow/knee collapse, candy-wrapper twisting, detached vertices, and weight bleeding.

### Acceptance criteria

A rig is not considered valid merely because it has bones; it must pass skin-weight and deformation validation.

### Expected tool calls

- pytest/numerical deformation tests;
- Blender headless pose rendering for integration QA;
- optional live auto-rigger;
- image inspection for contact sheets.

### Starter prompt

```text
Implement RetroModGen action item E4: skin-weight cleanup and deformation QA.

Treat low-poly deformation quality as a first-class requirement. Starting from E1-E3, normalize and prune skin weights, enforce max influences, detect invalid joint references and disconnected-part bleeding, and support a rigid/mechanical weighting mode plus an optional low-poly weight-sharpening pass.

Add analytic two-bone deformation tests and a deterministic pose-sweep QA system. When Blender is available, render a contact sheet of extreme poses; keep the numerical tests runnable without Blender/GPU. Run focused and full tests and report measured validation results.
```

---

## E5 — IK and animator control-rig generation

### Objective

Add useful inverse-kinematics controls without contaminating the portable deform skeleton or making animation dependent on one DCC package.

### Design rule

Maintain two layers:

```text
Control rig / IK rig
        ↓ drives
Deform skeleton
        ↓ skins
Mesh
```

The deform bones remain the runtime/export skeleton. IK target, pole, and helper controls are authoring tools.

### Initial IK chains

For humanoid rigs when semantic roles are available:

```text
left/right arm   shoulder -> elbow -> wrist/hand
left/right leg   hip -> knee -> ankle/foot
optional foot controls
optional look/head target
```

For non-humanoids, create IK only where the semantic/archetype definition declares a compatible chain.

### Implementation steps

1. Define backend-independent `IKChainSpec`:
   - chain root/end semantic roles or explicit bone IDs;
   - target;
   - pole target;
   - chain length;
   - joint limits;
   - optional stretch policy.
2. Generate control objects/helper bones in the selected authoring backend.
3. Implement humanoid arm/leg IK templates first.
4. Add pole-vector placement with deterministic fallback.
5. Add basic joint-limit support.
6. Ensure IK drives only the deform skeleton and does not change skin weights.
7. Add FK/IK bake path so final animation can be stored only on deform bones.
8. Store control-rig metadata in an authoring artifact/manifest; do not assume generic GLB will preserve every DCC constraint.
9. Keep an FK-only fallback if IK generation fails.

### Tests

Use an analytic two-bone chain and a synthetic leg rig:

- target reachable -> end effector reaches target within tolerance;
- unreachable target obeys stretch/clamp policy;
- pole target selects correct bend plane;
- joint limits honored;
- deterministic target/pole placement;
- baking IK -> FK produces equivalent deform-bone pose within tolerance;
- deleting control rig leaves deform skeleton and skin intact.

### Verification

In Blender headless/interactive smoke testing:

1. move both hand IK targets;
2. move both foot IK targets;
3. move elbow/knee poles;
4. bake the result to deform bones;
5. disable/remove controls;
6. verify the baked animation is visually unchanged.

### Acceptance criteria

A humanoid rig can be posed using IK for arms and legs, then baked into portable skeletal animation without requiring the control rig at runtime.

### Expected tool calls

- Blender armature/IK documentation lookup;
- Blender CLI for integration tests;
- offline analytic solver/transform tests;
- GLB validation after baked export.

### Starter prompt

```text
Implement RetroModGen action item E5: IK and animator control-rig generation.

Keep a strict separation between control/IK bones and the portable deform skeleton. Use semantic bone roles from E3. Implement v1 humanoid two-bone IK for arms and legs with deterministic targets/poles, optional joint limits, and an FK-only fallback. Add a bake step that writes the solved motion onto deform bones so runtime GLB does not depend on DCC-specific IK constraints.

Write analytic IK tests for reachable/unreachable targets, pole-vector bend direction, limits, and IK->FK bake equivalence. Add a Blender integration smoke test when Blender is available. Consult current Blender IK documentation rather than guessing APIs. Run full offline tests regardless of Blender availability.
```

---

## E6 — Skeletal animation import, authoring, and retargeting

### Objective

Make animation reusable across generated characters rather than requiring every rigged model to be animated from scratch.

### Implementation steps

1. Extend clip metadata:
   - name;
   - source range;
   - target FPS;
   - loop flag;
   - root-motion mode;
   - events/tags where needed.
2. Import skeletal clips from supported interchange assets.
3. Build semantic-role-based bone correspondence.
4. Retarget rotations/translations with rest-pose correction.
5. Handle scale/limb-length differences explicitly.
6. Define root-motion policy.
7. Preserve unmapped bones in rest pose unless a profile says otherwise.
8. Allow procedural/IK-authored poses to be baked as clips.
9. Add a small standard retro character clip set fixture:
   - idle;
   - walk;
   - attack;
   - pain;
   - death.

### Tests

- retarget identical skeleton -> numerically equivalent animation;
- renamed bones with same semantic roles -> equivalent result;
- different limb lengths -> end-effector/path tolerance checks;
- missing optional bone handled safely;
- root motion obeys policy;
- clip looping metadata survives serialization.

### Verification

Retarget one walk and one attack clip between two differently proportioned low-poly humanoid fixtures and inspect foot sliding, limb inversion, and root motion.

### Acceptance criteria

Animation logic consumes semantic roles and rest transforms, not assumptions about one auto-rigger's names.

### Expected tool calls

- local math/fixture tests;
- Blender CLI for visual integration verification;
- current glTF/Blender docs where animation import/export behavior matters.

### Starter prompt

```text
Implement RetroModGen action item E6: skeletal animation import and retargeting.

Build on the canonical deform skeleton and semantic role map. Add clip metadata, root-motion policy, animation import, semantic correspondence, rest-pose correction, and a deterministic retarget path. Do not tie retargeting to TokenRig/UniRig bone names.

Create two intentionally different humanoid fixture rigs and prove identical-role retargeting numerically, including root motion and missing optional bones. Add Blender visual verification when available and run the complete suite.
```

---

## E7 — Skeletal GLB export and rig round-trip validation

### Objective

Export generated characters as portable bone-rigged GLB assets and prove the skin survives independent reload.

### Required portable data

For glTF/GLB, validate at minimum:

```text
joint node hierarchy
skin.joints
inverseBindMatrices
JOINTS_0
WEIGHTS_0
animation channels targeting joint TRS
```

If more than four joint influences are ever supported, handle additional `JOINTS_n`/`WEIGHTS_n` sets deliberately rather than implicitly.

### Implementation steps

1. Export frozen mesh + materials + deform skeleton + skin weights.
2. Export bind pose/inverse bind matrices correctly.
3. Export animation clips on deform bones.
4. Exclude authoring-only helper/control bones unless explicitly requested.
5. Add an authoring sidecar/manifest describing IK/control rig provenance.
6. Reload the GLB independently and compare skeleton/skin data.
7. Validate with a Khronos-compatible glTF validator where practical.
8. Add a Blender import/export smoke test.

### Tests

- write/read rigged GLB fixture;
- joint hierarchy preserved;
- bind-pose skin deformation preserved;
- weights preserved within numeric tolerance;
- animation sample transforms preserved within tolerance;
- helper controls not accidentally included in runtime skeleton;
- malformed skin data rejected before export.

### Verification

Open one generated rigged character in Blender and the target runtime/editor (for example Godot when this becomes part of engine integration). Pose or play an animation and confirm the same deform skeleton drives the same mesh.

### Acceptance criteria

The primary modern output of a generated animated character is a valid **bone-rigged GLB**, not a vertex-animated mesh.

### Expected tool calls

- Khronos glTF specification/current validator documentation;
- local GLB parser/reloader tests;
- Blender CLI smoke tests;
- target-engine viewer/import smoke test when available.

### Starter prompt

```text
Implement RetroModGen action item E7: skeletal GLB export and rig round-trip validation.

Use the E1-E6 canonical deform skeleton. Export a standards-compliant skinned GLB with joint hierarchy, inverse bind matrices, JOINTS/WEIGHTS attributes, and animation channels on deform bones. Keep IK/control helpers out of the runtime skeleton by default and preserve their provenance in an authoring sidecar/manifest.

Verify current glTF 2.0 skinning requirements from Khronos. Add write/reload tests that compare hierarchy, weights, bind pose, and animation samples, plus Blender/validator smoke tests when available. Run the full suite.
```

---

## E8 — Skeletal animation to vertex-frame baker for MDL/MD2

### Objective

Bake the canonical bone-rigged animation into fixed-topology per-frame vertex positions suitable for MDL/MD2 while preserving the skeletal asset as the editable source of truth.

### Implementation steps

1. Load/evaluate the final skinned mesh and deform skeleton.
2. Ensure any IK/control-rig motion has first been baked to deform bones.
3. Sample skeletal animation at configured FPS.
4. Produce ordered vertex positions for every frame.
5. Verify vertex/index stability.
6. Calculate animation bounds.
7. Feed frame arrays to MDL/MD2 exporters.
8. Compare baked vertex positions against direct skin evaluation before format quantization.
9. Preserve modern skeletal GLB and optional authoring rig outputs in parallel.

### Recommended first implementation

Use Blender headless or another proven evaluator for integration validation rather than implementing every DCC constraint evaluator. The core numerical skinning evaluator should still be testable on simple fixtures without Blender.

### Tests

Use a tiny synthetic rig:

- 2 deform bones;
- optional IK control chain whose motion is baked first;
- simple hinge animation;
- known vertex positions at key samples.

Validate sampled positions numerically before MDL/MD2 quantization.

### Verification

Export one character with:

```text
idle
walk
attack
death
```

and view the same animation in:

```text
bone-rigged GLB
MD2 or MDL vertex-frame output
```

### Acceptance criteria

One frozen mesh and canonical skeletal rig can produce both modern skeletal output and classic vertex-frame output. MDL/MD2 never become the editable animation source.

### Expected tool calls

- Blender CLI or selected animation evaluator;
- automated numerical skinning fixture tests;
- MDL/MD2 validator;
- viewer smoke tests.

### Starter prompt

```text
Implement RetroModGen action item E8: canonical skeletal-animation to fixed-topology vertex-frame baking.

Use the E1-E7 bone-rigged asset as the source of truth. Ensure IK/control animation is baked to deform bones first, then sample configured clips/FPS into ordered vertex arrays, verify topology stability, compute bounds, and feed the frame data to MDL/MD2 exporters while retaining the skeletal GLB.

Build a tiny synthetic two-bone rig with numerically checkable deformations, compare baked frames against direct skin evaluation before format quantization, and run one viewer smoke test if available. Run the full suite.
```

---

# Phase F — LLM and vision authoring loop

## F1 — Natural-language request to AssetSpec

### Objective

Use an LLM as an **intent compiler**, not as the owner of mesh-processing logic.

### Implementation steps

1. Define JSON-schema/Pydantic output contract.
2. Provide profile information and legal ranges to the model.
3. Require structured output.
4. Validate model output with Pydantic/profile rules.
5. Resolve hard-profile constraints deterministically after model output.
6. Preserve user overrides.
7. Store model/provider/version and source request in provenance.
8. Add a manual/non-LLM path with identical `AssetSpec` output.

### Tests

Most tests should not call a paid/live LLM.

Test:

- parser/validator using stored responses;
- invalid model output;
- out-of-range values;
- profile hard-limit override;
- user override precedence.

### Live verification

Example input:

```text
Create a Quake II-style maintenance robot with one claw arm and one plasma cutter,
rusted yellow paint, about 700 triangles, and a 128x128 texture.
```

Verify the resulting spec is valid and reproducible as JSON.

### Acceptance criteria

The rest of RetroModGen cannot tell whether an AssetSpec came from ChatGPT, another model, a UI form, or a handwritten JSON file.

### Expected tool calls

- configured model/API only for live integration test;
- local schema/unit tests always;
- provider documentation lookup if structured-output API details are current-sensitive.

### Starter prompt

```text
Implement RetroModGen action item F1: natural-language request -> validated AssetSpec.

Treat the LLM as an intent compiler only. Use the existing Pydantic AssetSpec/profile system as the source of truth and require structured output. Hard profile constraints must be enforced by deterministic code after model output. Preserve user overrides and store model/provider/version provenance.

Do not make unit tests depend on a live paid model; use stored responses and invalid-response fixtures. Add one optional live smoke-test command and run all offline tests.
```

---

## F2 — Deterministic preview + vision critique into structured changes

### Objective

Let a vision model evaluate rendered candidates without directly editing mesh binaries.

### Pipeline

```text
compiled candidate
  -> deterministic turntable/contact sheet
  -> vision critique
  -> structured critique
  -> proposed AssetSpec/compiler delta
  -> user approval or next iteration
```

### Critique schema

Examples:

```text
silhouette_readability
texture_readability
important_feature_legibility
modern_vs_retro_style_mismatch
observed_artifacts
recommended_parameter_changes
confidence
```

### Tests

- parse stored critique responses;
- reject unsupported direct binary mutation instructions;
- validate suggested parameter ranges;
- ensure user approval boundary exists before destructive replacement of a selected asset.

### Acceptance criteria

Vision results produce **proposals**, not arbitrary code or direct mesh mutation.

### Expected tool calls

- preview renderer;
- optional vision model for live test;
- local stored-response tests.

### Starter prompt

```text
Implement RetroModGen action item F2: preview-driven vision critique.

Use deterministic preview renders as the only visual input to the critic. Define a structured critique/result schema containing observed problems and proposed AssetSpec/compiler parameter changes. The vision model must never directly mutate mesh data or execute arbitrary instructions. Add stored-response tests and validation of proposed parameter ranges.

Keep live vision calls optional; run all offline tests and one live smoke test only when a configured vision provider is available.
```

---

# Phase G — Production hardening

## G1 — Content-addressed stage cache and provenance manifest

### Objective

Avoid rerunning expensive stages while making every asset reproducible and auditable.

### Cache key concept

```text
hash(
  stage_version,
  relevant AssetSpec subset,
  compiler/backend config,
  input file hashes,
  backend/model/workflow version
)
```

### Implementation steps

1. Define a stage cache interface.
2. Implement local filesystem cache first.
3. Never cache only by filename.
4. Store stage metadata and checksums.
5. Add `--no-cache` and cache inspection/clear tools.
6. Store provenance manifest through the pipeline.

### Tests

- identical inputs hit cache;
- changed input bytes miss cache;
- changed spec field relevant to stage misses cache;
- irrelevant field may reuse cache where deliberately defined;
- corrupted cache entry is detected.

### Acceptance criteria

A repeated generation/compile clearly reports reused vs executed stages.

### Expected tool calls

- local hashing/file tests;
- no external services needed.

### Starter prompt

```text
Implement RetroModGen action item G1: content-addressed stage cache and provenance.

Inspect stage boundaries first. Add a small local filesystem cache keyed by stage version, relevant AssetSpec/config fields, input hashes, and backend/model/workflow identifiers. Never key by filename alone. Add corruption detection, --no-cache behavior, and clear provenance showing which stages were reused.

Write cache hit/miss/corruption tests and run the full suite.
```

---

## G2 — CI matrix that does not require GPU/model software

### Objective

Make every pull request automatically validate the deterministic core.

### Minimum CI jobs

```text
Python core tests
lint/format/type checks
native C++ build/tests
fixture compile smoke test
```

Optional/manual jobs:

```text
ComfyUI live integration
GPU model generation
Blender integration if too heavy for default CI
```

### Implementation steps

1. Configure supported Python matrix conservatively.
2. Cache Python dependencies, not generated model outputs.
3. Build native module on at least Windows and/or Linux as practical.
4. Run mock-backend end-to-end smoke test.
5. Upload failure diagnostics/artifacts where useful.

### Acceptance criteria

A normal PR gets strong confidence without downloading multi-gigabyte model weights.

### Expected tool calls

- GitHub Actions docs if syntax/current images require verification;
- workflow runs/log inspection;
- local equivalent commands where possible.

### Starter prompt

```text
Implement RetroModGen action item G2: core CI matrix.

Create CI that validates the project without GPU/model downloads: Python tests, lint/type/format checks already adopted by the repo, native build/tests, and an end-to-end mock-backend compile smoke test. Keep ComfyUI/Hunyuan/TRELLIS/Blender-heavy jobs optional or manually triggered unless they can run cheaply and reliably.

Run equivalent commands locally where possible, validate workflow syntax, and inspect the first CI run rather than assuming it passes.
```

---

## G3 — Regression corpus and quantitative quality metrics

### Objective

Prevent visual/geometry quality from drifting as simplification algorithms evolve.

### Corpus categories

```text
boxy prop
round prop
thin appendage/weapon
asymmetric prop
UV-seam-heavy mesh
hard-edge-heavy mesh
simple humanoid
```

### Metrics

At minimum track:

- triangle/vertex counts;
- Hausdorff or sampled surface distance where practical;
- normal deviation;
- silhouette proxy error;
- UV seam loss;
- semantic-region error;
- texture palette error/readability metrics where useful;
- compile time;
- peak memory where easy to measure reliably.

### Implementation steps

1. Build redistributable/generated corpus.
2. Record baseline metrics in versioned data.
3. Add threshold-based regression tests.
4. Generate optional HTML/Markdown comparison report.
5. Avoid enforcing subjective “looks better” claims without supporting metrics/preview evidence.

### Acceptance criteria

A simplifier change that destroys a thin weapon or face-weighted area is detected before merge.

### Expected tool calls

- local benchmark execution;
- preview artifact generation;
- no model generation required.

### Starter prompt

```text
Implement RetroModGen action item G3: regression corpus and quantitative compiler metrics.

Create a small redistributable/generated mesh corpus covering boxy, rounded, thin-feature, asymmetric, UV-seam, hard-edge, and simple humanoid cases. Add versioned baseline metrics for geometry/feature preservation and threshold-based regression checks. Include preview/report generation where useful, but do not replace numerical regression checks with subjective screenshots alone.

Run the corpus against both baseline and current custom simplifiers and summarize results.
```

---

## G4 — Packaging, release artifacts, and reproducibility metadata

### Objective

Make RetroModGen installable and make generated assets explain how they were produced.

### Deliverables

- clean Python package build;
- native extension packaging strategy;
- version command;
- output manifest schema/version;
- release notes template;
- reproducible dependency lock strategy appropriate to the project;
- optional container recipe for inference/client environment only if it becomes useful.

### Tests

```bash
python -m build
# install wheel into clean venv
pip install dist/<wheel>
retromodgen --version
retromodgen profiles
pytest or smoke-test installed package
```

### Acceptance criteria

A release artifact can be installed into a clean environment and can run the Comfy-free core without source checkout assumptions.

### Expected tool calls

- package build/install commands;
- GitHub release tooling when a release is requested;
- no need to bundle models.

### Starter prompt

```text
Implement RetroModGen action item G4: packaging and reproducible release artifacts.

Inspect the current pyproject and native build. Produce an installable wheel/package strategy that keeps large models and ComfyUI external. Add `retromodgen --version`, manifest/schema versioning, and clean-environment wheel smoke tests. Do not embed model weights or machine-specific paths.

Build the package, install it into a fresh environment, run the documented smoke commands, and report the exact results.
```

---

# 8. Phase gates

Do not start a later phase merely because code can be written. Use these gates.

## Gate A — Core harness ready

Required:

- A1-A5 complete;
- core install has no model requirement;
- mock backend end-to-end path works;
- CI can exercise the pipeline offline.

## Gate UI — ComfyUI authoring surface ready

Required:

- UI1-UI3 complete;
- ComfyUI source is pinned/reproducible through the submodule + lock file;
- core test suite still passes with the submodule absent;
- RetroModGen custom nodes are visible through `/object_info`;
- the spec/profile validation graph runs without a GPU model;
- UI4-UI6 may continue incrementally as corresponding core stages land.

## Gate B — Static-prop vertical slice ready

Required:

- B1-B6 complete;
- UI1-UI3 complete and the relevant UI4 static-asset adapters exist;
- one real source generator works through the backend API or an equivalent versioned Comfy graph;
- source mesh can be compiled without ComfyUI afterward;
- one `quake2_prop` output passes validation;
- one Comfy graph performs source -> RetroModGen compile -> validated GLB;
- source/final metrics and manifest exist.

## Gate C — Custom retro geometry ready

Required:

- C1-C3 stable against regression corpus;
- custom simplifier beats or meaningfully differs from baseline on purpose-built preservation metrics;
- native C++ port is optional until profiling justifies it, but once C4 starts it must preserve reference behavior.

## Gate D — Native format ready

Required for each format independently:

- reader;
- writer;
- hard-limit validator;
- round-trip tests;
- independent viewer/engine smoke test.

## Gate E — Bone-rigged character path ready

Required:

- E1-E8 complete or any explicitly deferred optional live-backend integrations documented;
- topology freeze and rig invalidation rules enforced;
- at least one automatic or template rigging backend plus `MockRiggingBackend`;
- valid deform skeleton and normalized skin weights;
- deformation QA pass;
- arm/leg IK for the supported humanoid profile with IK -> deform-bone bake;
- skeletal animation/retarget path;
- bone-rigged GLB round-trip passes;
- deterministic skeletal -> vertex-frame baking;
- one dual-export animated character whose GLB remains the editable/canonical source.

## Gate F — AI authoring loop ready

Required:

- manual AssetSpec path remains functional;
- LLM output is validated structured data;
- vision critic only proposes structured changes;
- no live model is required for core tests.

---

# 9. End-to-end verification scenarios

These scenarios should remain runnable throughout development.

## Scenario 1 — Offline fixture compile

Purpose: core health check.

```text
AssetSpec
  -> MockGeometryBackend
  -> normalized fixture
  -> simplifier
  -> texture compiler
  -> GLB
  -> validator
```

Command target:

```bash
retromodgen generate examples/quake2_crate.asset.json \
  --backend mock \
  --output build/e2e-mock
```

Pass conditions:

- no network access required;
- no ComfyUI required;
- output GLB reopens;
- validation passes;
- manifest records mock backend and compiler versions.

## Scenario 2 — Live Comfy node/editor + source generation

Purpose: adapter/inference health check.

```text
reference image
  -> ComfyUI
  -> selected 3D model
  -> source GLB
```

Pass conditions:

- backend health succeeds;
- job submission succeeds;
- generated file is retrieved;
- source asset can be inspected by RetroModGen.

## Scenario 3 — Full static Quake-II-style prop

Purpose: Phase B gate.

```text
reference image
  -> source generator
  -> normalization
  -> low-poly simplification
  -> 128x128 texture
  -> GLB export
  -> profile validation
  -> preview
```

Pass conditions:

- target triangle budget satisfied;
- texture budget satisfied;
- GLB valid;
- no manual Blender editing required;
- preview clearly shows the final asset.

## Scenario 4 — MD2 static/frame round trip

Purpose: format integrity.

```text
fixed topology frames
  -> MD2 writer
  -> MD2 reader
  -> compare topology/frames
```

Pass conditions:

- header/offset validation passes;
- frame count and vertex topology preserved;
- quantization error reported and within configured tolerance;
- independent viewer loads it.

## Scenario 5 — Bone-rigged animated character dual export

Purpose: character/rigging gate.

```text
low-poly final character
  -> topology freeze
  -> skeleton generation/import
  -> skin weights + deformation QA
  -> IK/control rig
  -> skeletal animation/retarget
  -> bake control motion to deform bones
  -> bone-rigged GLB export
  -> vertex-frame bake
  -> MD2 or MDL export
```

Pass conditions:

- both outputs come from the same frozen topology and canonical deform skeleton;
- skeleton hierarchy and skin weights validate;
- max influences/weight normalization satisfy the profile;
- humanoid arm/leg IK reaches test targets and bakes to equivalent deform-bone poses;
- GLB round-trip preserves joints, weights, rest pose, and clips;
- configured clips exist;
- frame counts respect format limits;
- vertex-frame samples match skeletal deformation within tolerance before format quantization;
- animations are visually recognizable in both viewers.

---

# 10. Testing strategy

## 10.1 Unit tests

Use for:

- schemas;
- profiles;
- backend registry;
- workflow patching;
- mesh math;
- texture algorithms;
- binary readers/writers;
- cache keys;
- format limits.

## 10.2 Fixture tests

Use deterministic local assets for:

- mesh sanitation;
- simplification;
- UV preservation;
- semantic weighting;
- animation sampling;
- exporters.

## 10.3 Rigging and animation fixture tests

Maintain tiny deterministic assets specifically for rigging math:

```text
two_bone_strip.glb          analytic skinning fixture
humanoid_minimal.glb        semantic role + arm/leg IK fixture
robot_hinge.glb             rigid/mechanical weighting fixture
creature_branch.glb         non-humanoid hierarchy fixture
```

Core tests must be able to validate hierarchy, weights, linear-blend skinning, simple IK math, and animation sampling without a GPU or live auto-rigger. Blender/live rigging integrations are additional integration tests, not substitutes for these fixtures.

## 10.4 Golden-data tests

Appropriate for:

- small binary headers;
- known palette transforms;
- deterministic procedural fixtures;
- structured manifests.

Do not overuse exact binary golden files for library-generated GLB where nonsemantic ordering may vary.

## 10.5 Integration tests

Comfy integration has two tiers:

```text
offline: import/mapping/workflow/API-contract tests with no Comfy process
live:    pinned submodule health + /object_info + workflow execution
```

The default suite must never require the submodule, CUDA, or model weights. Mark live tests with `comfy_live`.


Mark optional integrations separately:

```text
integration_comfy
integration_blender
integration_gpu
integration_rigging_gpu
integration_tokenrig
```

Default CI should skip these unless the environment explicitly enables them.

## 10.6 End-to-end tests

At least one end-to-end path must use only the mock backend so the complete pipeline is continuously testable.

## 10.7 Visual regression

Use rendered images as supporting evidence, not the only correctness test.

Where practical calculate metrics and retain contact sheets for human inspection.

---

# 11. Verification checklist for coding agents

Before marking any item complete, answer all applicable questions:

```text
[ ] Did I inspect current code before modifying it?
[ ] Did I avoid duplicating an existing helper/interface?
[ ] Does core import still work without ComfyUI/model packages?
[ ] Did I add tests for new behavior?
[ ] Did focused tests pass?
[ ] Did the complete test suite pass?
[ ] Did I execute the relevant CLI/API path manually?
[ ] Did I inspect/reload generated artifacts where applicable?
[ ] Are hard profile limits enforced?
[ ] Are optional dependencies handled gracefully?
[ ] Did I update documentation/config examples?
[ ] Did I record commands actually run?
[ ] Did I avoid unrelated refactors?
```

For algorithm changes additionally:

```text
[ ] Did I compare against the current baseline?
[ ] Did I add a regression fixture for the failure/improvement?
[ ] Are repeated results deterministic?
[ ] Did I verify no NaN/Inf/invalid indices were introduced?
```

For file-format changes additionally:

```text
[ ] Did I verify against an authoritative specification/source?
[ ] Is malformed input rejected safely?
[ ] Do round-trip tests pass?
[ ] Was an independent viewer/engine smoke test performed when possible?
```

For skeletal-rigging/animation changes additionally:

```text
[ ] Is topology frozen before skin binding?
[ ] Is the bone hierarchy acyclic and structurally valid?
[ ] Are skin weights finite, normalized, and within the influence limit?
[ ] Does rest-pose skinning reproduce the undeformed mesh within tolerance?
[ ] Did deformation/pose-sweep QA pass?
[ ] Are semantic bone roles independent of backend-specific names?
[ ] Are IK/control bones separated from the portable deform skeleton?
[ ] Does IK -> deform-bone baking preserve the pose within tolerance?
[ ] Does rigged GLB reload with equivalent joints/weights/animations?
[ ] If MDL/MD2 is involved, do baked vertex frames match skeletal evaluation before quantization?
```

---

### Additional ComfyUI checks when applicable

- [ ] Did I inspect the exact pinned ComfyUI source/official documentation rather than assuming an older API?
- [ ] Did I avoid changing the Comfy gitlink/pin unless the task explicitly required it?
- [ ] Is the custom node only an adapter around a tested core function?
- [ ] Does the same functionality still work without ComfyUI?
- [ ] Do `/system_stats` and `/object_info` pass when live verification is available?
- [ ] Is the Comfy commit recorded in integration/provenance evidence?
- [ ] Are workflow files free of machine-specific paths, secrets, and model weights?

---

# 12. Standard coding-agent prompt prefix

The following prefix can be prepended to any action-item starter prompt.

```text
You are implementing one scoped action item in the RetroModGen repository.

Rules:
1. Inspect the current repository and relevant docs before changing code. Do not assume the scaffold is unchanged.
2. Keep ComfyUI, model weights, CUDA, and Blender optional unless this action item explicitly tests one of them.
3. Do not overengineer. Reuse existing interfaces and keep changes scoped.
4. Search current official upstream documentation/source when implementing an external API or binary format.
5. Add focused automated tests with every behavior change.
6. Run focused tests first, then the complete test suite.
7. Run the relevant CLI/integration verification command where applicable.
8. Do not claim success without command/output evidence.
9. If an external service is unavailable, complete mocks/offline work and state exactly which live test remains unexecuted.
10. For characters/creatures/articulated assets, treat the deform skeleton + skin weights as canonical; keep IK/control-rig data separate and bake controls to deform bones for portable runtime export.
11. At the end, summarize files changed, tests/commands run, resulting metrics/artifacts, and any follow-up risks.
```

---

# 13. Suggested first work session

The recommended immediate sequence from the current scaffold is:

```text
1. A1 dependency/bootstrap cleanup
2. A2 backend registry
3. A3 mock backend + fixtures
4. A4 orchestrator
5. A5 CLI
6. UI1 initialize/pin the ComfyUI submodule
7. UI2 harden the retromodgen_comfy node contract
8. UI3 complete the no-GPU spec/profile/validation graph
```

A1-A5 still do not require ComfyUI. After Gate A, initialize the submodule and complete UI1-UI3 before depending on real inference workflows. This gives the project a working node-editor surface early while preserving a Comfy-free core and CI path.

---

# 14. Recommended first milestone

**Milestone 0.1 — Offline Retro Compiler Harness**

Release requirements:

```text
[x] AssetSpec/profile system
[ ] dependency groups finalized
[ ] backend registry
[ ] deterministic mock backend
[ ] pipeline orchestration
[ ] CLI generate/compile/inspect
[ ] normalized mesh import
[ ] baseline simplifier
[ ] retro texture compiler v1
[ ] GLB export
[ ] profile validation report
[ ] deterministic preview or documented optional preview
[ ] CI mock end-to-end test
```

The milestone is intentionally useful without any AI model installed:

```text
input GLB/fixture
   -> RetroModGen
   -> validated low-poly retro GLB
```

**Milestone 0.2 — First ComfyUI-Assisted Prop** then adds:

```text
pinned ComfyUI submodule
RetroModGen custom nodes visible in the editor
no-GPU spec/profile validation graph
ComfyUI external API client
one image-to-3D workflow
one real generated source asset
source -> RetroModGen nodes/core -> validated retro GLB
```

**Milestone 0.3 — First Bone-Rigged Generated Character** then adds:

```text
one generated low-poly character
  -> frozen topology
  -> automatic/template skeleton
  -> normalized low-poly skin weights
  -> deformation QA
  -> humanoid arm/leg IK controls
  -> IK/FK motion baked to deform bones
  -> bone-rigged GLB
  -> at least one retargeted or authored animation
  -> optional MD2/MDL vertex-frame bake
```

Milestone 0.3 is complete only when the GLB can be reloaded in an independent tool and the skeleton, skinning, and animation still function.

Only after Milestones 0.1 and 0.2 should the project invest heavily in custom QEM/native formats. Phase E should begin when the static character topology pipeline is stable; model fine-tuning remains later than a working rigged-character vertical slice.
