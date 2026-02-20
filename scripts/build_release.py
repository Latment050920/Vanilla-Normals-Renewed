#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_existing(src: Path, dst: Path) -> None:
    for p in src.rglob('*'):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_symlink() and not p.exists():
            continue
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif p.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def main() -> None:
    parser = argparse.ArgumentParser(description='Build release zip for resource pack.')
    parser.add_argument('--pack-name', default='VanillaNormalsRenewed')
    parser.add_argument('--version', default='1.0.0')
    parser.add_argument('--mc-version', default='1.21.11')
    args = parser.parse_args()

    out_dir = Path('release')
    out_dir.mkdir(parents=True, exist_ok=True)

    archive_base = out_dir / f"{args.pack_name}_PBR_512x_{args.mc_version}_v{args.version}"
    archive_zip = archive_base.with_suffix('.zip')
    if archive_zip.exists():
        archive_zip.unlink()

    include = ['assets', 'pack.mcmeta', 'pack.png', 'LICENSE', 'README.md', 'docs']
    staging = Path('.build_release_tmp')
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    for name in include:
        p = Path(name)
        if not p.exists():
            continue
        dest = staging / p
        if p.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            copy_existing(p, dest)
        elif p.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)

    shutil.make_archive(str(archive_base), 'zip', root_dir=staging)
    shutil.rmtree(staging)
    print(f'Built {archive_zip}')


if __name__ == '__main__':
    main()
