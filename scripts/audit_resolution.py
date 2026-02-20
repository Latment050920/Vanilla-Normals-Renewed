#!/usr/bin/env python3
from __future__ import annotations

import csv
import struct
from pathlib import Path

ROOT = Path('assets/minecraft/textures')
TARGETS = [ROOT / 'block', ROOT / 'item']
OUT = Path('reports/resolution_audit.csv')


def png_size(path: Path):
    try:
        with path.open('rb') as f:
            if f.read(8) != b'\x89PNG\r\n\x1a\n':
                return None
            _len = struct.unpack('>I', f.read(4))[0]
            if f.read(4) != b'IHDR':
                return None
            w, h = struct.unpack('>II', f.read(8))
            return w, h
    except FileNotFoundError:
        return None


def category(path: Path) -> str:
    s = path.stem
    if s.endswith(('_n', '_s', '_e')):
        return 'pbr_map'
    return 'base'


rows = []
for d in TARGETS:
    if not d.exists():
        continue
    for p in d.rglob('*.png'):
        size = png_size(p)
        if size is None:
            continue
        w, h = size
        status = 'ok_512' if w == 512 else ('above_512' if w > 512 else 'below_512')
        rule = '512-block-item'
        rows.append([p.as_posix(), w, h, category(p), status, rule])

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='', encoding='utf-8') as f:
    wr = csv.writer(f)
    wr.writerow(['path', 'width', 'height', 'category', 'status', 'rule'])
    wr.writerows(rows)

print(f'Wrote {OUT} with {len(rows)} rows')
