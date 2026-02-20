# 资产与 PBR 规范诊断报告

## 目录资产概览
- 纹理总数(PNG): 2722
- block: 1913, item: 521, other: 288

## PBR 命名规范检测
- base: 909
- _n(normal): 907
- _s(spec/packed): 906
- _e(emissive): 0
- 判定：当前包以 LabPBR/OptiFine 双兼容命名为主（`_n/_s` 已全面覆盖，`_e` 有待系统化扩展）。

## 分辨率分布（按宽度）
- 8px: 2
- 16px: 2193
- 32px: 4
- 48px: 9
- 64px: 178
- 128px: 34
- 256px: 2

## 1.21.11 兼容性结论
- `pack.mcmeta` 已为 `pack_format=75`。
- `assets/minecraft/optifine/texture.properties` 使用 `format=lab-pbr/1.3`。
- `assets/minecraft/optifine/emissive.properties` 启用 `_e`。

## 风格化改造建议（赛博符箓・工业终端）
1. 先处理英雄方块 30+（石材/木材/金属/玻璃冰/红石/矿物），确保宏观差异明显。
2. 用参数化主题(theme.json)统一控制 normal、roughness、AO、微细节频率、符箓线密度与发光等级。
3. 再扩全包并以脚本复刻。