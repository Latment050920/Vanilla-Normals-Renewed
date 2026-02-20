# Vanilla-Normals-Renewed

Vanilla style PBR resource pack, upgraded workflow for **Minecraft Java 1.21.11** with automated **512x** and LabPBR-oriented processing.

## Quick facts
- Target version: **1.21.11** (`pack_format=75`)
- Recommended loader/shaders: **Iris** (preferred), OptiFine compatible
- PBR format: `lab-pbr/1.3` (`assets/minecraft/optifine/texture.properties`)
- Emissive suffix: `_e` (`assets/minecraft/optifine/emissive.properties`)

## Naming and channel rules
- `*_n.png`: normal map
- `*_s.png`: packed PBR map
  - R = AO
  - G = Roughness
  - B = Metalness
  - A = Height
- `*_e.png`: emissive map

## Automation scripts
```bash
python scripts/run_all.py
```

### Individual steps
```bash
python scripts/upgrade_to_512.py --target 512
python scripts/enhance_pbr.py --emissive-level 3
python scripts/audit_resolution.py
python scripts/audit_references.py
python scripts/build_release.py --version 1.21.11-1
```

## Reports
Generated into `reports/`:
- `compatibility_report.md`
- `resolution_audit.csv`
- `missing_reference_report.txt`

## Release output
Generated locally into `release/`:
- `PackName_PBR_512x_1.21.11_vX.Y.Z.zip`

> Note: repository no longer commits binary zip artifacts; build with `python scripts/build_release.py`.
