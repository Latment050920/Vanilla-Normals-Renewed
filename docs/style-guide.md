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

## 生产流程（阶段化）
1. 英雄方块阶段：
   ```bash
   python scripts/enhance_pbr.py --phase hero --theme theme.json --emissive-level 4
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
