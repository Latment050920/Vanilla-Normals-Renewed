#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path('.')
TEX_ROOT = ROOT / 'assets/minecraft/textures'
OUT = ROOT / 'reports/missing_reference_report.txt'

refs = []

# Scan json-like files if present
for p in ROOT.rglob('*.json'):
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if isinstance(v, (dict, list)):
                    stack.append(v)
                elif isinstance(v, str) and (k in {'texture', 'textures'} or 'texture' in k):
                    refs.append((p, v))
        elif isinstance(cur, list):
            stack.extend(cur)

# Scan .properties for texture= style refs
prop_pattern = re.compile(r'(?:texture|source|src)\s*=\s*([\w:/.-]+)')
for p in ROOT.rglob('*.properties'):
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        m = prop_pattern.search(line)
        if m:
            refs.append((p, m.group(1)))

missing = []
for src, ref in refs:
    if ref.startswith('#'):
        continue
    ref = ref.replace('minecraft:', '')
    if ref.startswith('textures/'):
        rel = ref
    else:
        rel = f'textures/{ref}' if '/' in ref else f'textures/{ref}'
    if not rel.endswith('.png'):
        rel = rel + '.png'
    target = ROOT / 'assets/minecraft' / rel
    if not target.exists():
        missing.append((src.as_posix(), ref, target.as_posix()))

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', encoding='utf-8') as f:
    f.write('Missing texture reference report\n')
    f.write(f'Total references scanned: {len(refs)}\n')
    f.write(f'Missing references: {len(missing)}\n\n')
    for s, r, t in missing:
        f.write(f'{s} -> {r} (missing: {t})\n')

print(f'Wrote {OUT}. missing={len(missing)} scanned={len(refs)}')
