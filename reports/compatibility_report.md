# compatibility_report (Minecraft 1.21.11)

## 1) 元数据兼容
- 已将 `pack.mcmeta` 升级至 `pack_format=75`，并添加 `supported_formats` 区间（55–75）。

## 2) 路径与结构扫描结果
- 当前仓库以 `assets/minecraft/textures/**` + `assets/minecraft/optifine/**` 为主。
- 未发现 `assets/minecraft/models/**`、`assets/minecraft/atlases/**`、`assets/minecraft/shaders/**` 自定义覆盖文件；因此不存在本仓库内旧版 `gui/sprites` 或 atlas JSON 自定义迁移冲突。
- `audit_references.py` 扫描 JSON/Properties 引用：当前未发现纹理引用缺失（详见 `missing_reference_report.txt`）。

## 3) 1.21.x 兼容修复点
- 新增/确认 LabPBR 标识：`assets/minecraft/optifine/texture.properties` (`format=lab-pbr/1.3`)。
- 新增 emissive 规则：`assets/minecraft/optifine/emissive.properties` (`suffix.emissive=_e`)。
- 资源包元数据描述更新为 1.21.11 主版本。

## 4) 过时项 / 注意项
- 旧 `pack_format=15` 已废弃，不再适用于 1.21.11。
- 若后续加入 `models/atlas/gui` 自定义覆盖，需重新执行 `scripts/audit_references.py` 并补充 atlas 路径映射校验。
