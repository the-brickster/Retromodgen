# RetroModGen ComfyUI workflows

This directory stores versioned **API-format** workflow templates used for automation and
integration tests. UI workflow JSON exported by ComfyUI may also be kept here when useful,
but name the two formats explicitly.

Initial workflow:

- `spec_validate.api.json` — loads an `AssetSpec`, loads its target profile, and validates it
  using RetroModGen custom nodes. It exercises node discovery without requiring a GPU model.

As geometry backends are integrated, add workflows such as:

- `hunyuan_source_mesh.api.json`
- `trellis_source_mesh.api.json`
- `retro_static_prop.api.json`
- `retro_character_rigged_glb.api.json`

Do not hard-code machine-specific absolute paths or model directories in committed workflows.
Use workflow placeholders/configuration resolution before submission.
