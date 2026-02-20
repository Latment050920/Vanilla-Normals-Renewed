#!/usr/bin/env python3
from __future__ import annotations

import subprocess

COMMANDS = [
    ['python', 'scripts/upgrade_to_512.py', '--target', '512'],
    ['python', 'scripts/enhance_pbr.py', '--emissive-level', '3'],
    ['python', 'scripts/audit_resolution.py'],
    ['python', 'scripts/audit_references.py'],
    ['python', 'scripts/build_release.py', '--version', '1.21.11-1'],
]

for cmd in COMMANDS:
    print('>>>', ' '.join(cmd))
    subprocess.run(cmd, check=True)

print('Pipeline complete.')
