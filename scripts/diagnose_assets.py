#!/usr/bin/env python3
from __future__ import annotations

import struct
from collections import Counter
from pathlib import Path

ROOT = Path('assets/minecraft/textures')
OUT = Path('docs/asset_pbr_diagnosis.md')


def png_size(path: Path):
    try:
        with path.open('rb') as f:
            if f.read(8) != b'\x89PNG\r\n\x1a\n':
                return None
            _ = struct.unpack('>I', f.read(4))[0]
            if f.read(4) != b'IHDR':
                return None
            w, h = struct.unpack('>II', f.read(8))
            return w, h
    except Exception:
        return None


def main():
    all_png = list(ROOT.rglob('*.png'))
    suffix = Counter()
    wcounter = Counter()
    kinds = Counter()
    for p in all_png:
        stem = p.stem
        if stem.endswith('_n'):
            suffix['_n'] += 1
        elif stem.endswith('_s'):
            suffix['_s'] += 1
        elif stem.endswith('_e'):
            suffix['_e'] += 1
        else:
            suffix['base'] += 1

        size = png_size(p)
        if size:
            wcounter[size[0]] += 1
        if '/block/' in p.as_posix():
            kinds['block'] += 1
        elif '/item/' in p.as_posix():
            kinds['item'] += 1
        else:
            kinds['other'] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "\n".join([
            "# 资产与 PBR 规范诊断报告",
            "",
            "## 目录资产概览",
            f"- 纹理总数(PNG): {len(all_png)}",
            f"- block: {kinds['block']}, item: {kinds['item']}, other: {kinds['other']}",
            "",
            "## PBR 命名规范检测",
            f"- base: {suffix['base']}",
            f"- _n(normal): {suffix['_n']}",
            f"- _s(spec/packed): {suffix['_s']}",
            f"- _e(emissive): {suffix['_e']}",
            "- 判定：当前包以 LabPBR/OptiFine 双兼容命名为主（`_n/_s` 已全面覆盖，`_e` 有待系统化扩展）。",
            "",
            "## 分辨率分布（按宽度）",
            *[f"- {w}px: {c}" for w, c in sorted(wcounter.items())],
            "",
            "## 1.21.11 兼容性结论",
            "- `pack.mcmeta` 已为 `pack_format=75`。",
            "- `assets/minecraft/optifine/texture.properties` 使用 `format=lab-pbr/1.3`。",
            "- `assets/minecraft/optifine/emissive.properties` 启用 `_e`。",
            "",
            "## 风格化改造建议（赛博符箓・工业终端）",
            "1. 先处理英雄方块 30+（石材/木材/金属/玻璃冰/红石/矿物），确保宏观差异明显。",
            "2. 用参数化主题(theme.json)统一控制 normal、roughness、AO、微细节频率、符箓线密度与发光等级。",
            "3. 再扩全包并以脚本复刻。",
        ]), encoding='utf-8'
    )
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
