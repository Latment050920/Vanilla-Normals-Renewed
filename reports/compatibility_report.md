# compatibility_report (Minecraft 1.21.11)

## 1) 元数据与规范
- `pack.mcmeta`：`pack_format=75`，主目标版本 1.21.11。
- PBR 规范：`assets/minecraft/optifine/texture.properties` -> `format=lab-pbr/1.3`。
- Emissive：`assets/minecraft/optifine/emissive.properties` -> `suffix.emissive=_e`。

## 2) 路径与引用扫描
- 扫描范围：json/properties 中纹理引用。
- 结果：`missing_reference_report.txt` 当前 `scanned=0, missing=0`（仓库主要为纯纹理资产分发）。

## 3) 1.21.x 兼容说明
- 仓库未自带 `models/atlases/shaders` 自定义覆盖，因此不存在本仓库内部 atlas 路径迁移冲突。
- 若后续增加模型/图集覆盖，需重新执行 `scripts/audit_references.py` 并扩展 atlas 规则校验。

## 4) 风格化管线升级（赛博符箓・工业终端）
- 新增 `theme.json` 参数化主题。
- 新增英雄方块清单 `scripts/hero_blocks.txt`（30+）。
- `scripts/enhance_pbr.py` 支持 `--phase hero|all`，可先英雄方块再全包扩展。
