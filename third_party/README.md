# Third-party source checkouts

`third_party/ComfyUI` is intended to be a Git submodule, not vendored source.

The scaffold ZIP cannot carry a Git submodule gitlink by itself. After initializing the
repository, run one of:

```powershell
python scripts/comfyui/bootstrap_submodule.py
```

```bash
python scripts/comfyui/bootstrap_submodule.py
```

The script creates/initializes the submodule and checks out the commit recorded in
`config/comfyui.lock.json`.

ComfyUI is separately licensed under GPL-3.0. Keep its upstream license and repository
history intact and review applicable distribution obligations before redistributing a
bundle that includes it.
