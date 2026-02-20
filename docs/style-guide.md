# 风格指南：赛博符箓・工业终端

## 核心视觉
- 基底：写实材质（PBR）
- 签名：细线符箓/电路纹（低覆盖率、高辨识）
- 发光：只给合理物理/功能部位（红石、矿物晶体、金属接缝铭牌、能量线路）
- 配色：枪灰/青蓝为主，朱砂色仅作高对比点缀

## 主题参数来源
- 文件：`theme.json`
- 关键参数：
  - `palette.primary/secondary/accent`
  - `pbr.normal_strength`
  - `pbr.roughness_contrast`
  - `pbr.ao_strength`
  - `microdetail.frequency`
  - `microdetail.edge_wear`
  - `microdetail.circuit_line_strength`
  - `emissive.level`
  - `item_reflectance.metal_item_boost/gem_item_boost/glass_item_boost`
  - `item_reflectance.clearcoat_strength`
  - `item_reflectance.anisotropy`

## 生产流程（阶段化）
1. 英雄方块阶段：
   ```bash
   python scripts/enhance_pbr.py --phase hero --theme theme.json --emissive-level 4 --include-items --force-item-reflective
   ```
2. 扩全包阶段：
   ```bash
   python scripts/enhance_pbr.py --phase all --theme theme.json --emissive-level 4 --include-items
   ```
3. 审计与打包：
   ```bash
   python scripts/audit_resolution.py
   python scripts/audit_references.py
   python scripts/build_release.py --version 1.21.11-style1
   ```

## 推荐光影设置
- Iris + Complementary Reimagined / BSL
- 开启：POM/normal/specular
- 关闭过度 bloom，避免细线符箓被糊化

## UI 分辨率策略
- `textures/block/**` + `textures/item/**` 目标 512x
- GUI/UI 建议保持原生，避免字体和布局失真


## 物品反光策略（新增）
- 金属类物品（锭/工具/盔甲）降低 roughness 并抬高 metalness，形成更明确镜面反射。
- 宝石类物品（钻石/绿宝石/紫水晶）使用中等金属度 + 低 roughness，营造高光清透感。
- 加入各向异性刷纹（anisotropic brush）以增强工业终端风格。
