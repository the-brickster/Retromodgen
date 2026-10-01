# MDL / MD2 Export Notes

This document records exporter design requirements. Hard limits must be verified against authoritative format/source references when implementation begins.

## Common requirements

- fixed topology across animated frames;
- deterministic vertex ordering;
- explicit coordinate-system conversion;
- explicit scale/origin policy;
- texture coordinate conversion;
- per-format vertex-position quantization;
- quantization error reporting;
- frame naming and clip-range metadata retained outside the binary when necessary.

## MDL exporter stages

```text
CompiledAsset
  -> validate MDL profile
  -> convert coordinate system
  -> quantize frame bounds/vertices
  -> convert skin/palette representation
  -> write header
  -> write skin data
  -> write texcoords
  -> write triangles
  -> write frames/groups
  -> reopen and parse for round-trip test
```

## MD2 exporter stages

```text
CompiledAsset
  -> validate MD2 profile
  -> convert coordinate system
  -> prepare skin names
  -> prepare ST coordinates
  -> preserve triangle indexing
  -> quantize each frame
  -> map/derive normal index where needed
  -> write GL command list if implementation requires/supports it
  -> reopen and parse for round-trip test
```

## Testing strategy

Implement readers before or alongside writers. A writer test should not only compare bytes; it should reparse the generated file and compare semantic data.

Add engine/viewer smoke tests later, but do not make an external GUI tool the unit-test oracle.
