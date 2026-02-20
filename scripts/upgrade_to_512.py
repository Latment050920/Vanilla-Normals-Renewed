#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageFilter

TARGET_DIRS = [
    Path("assets/minecraft/textures/block"),
    Path("assets/minecraft/textures/item"),
]


def is_exception(path: Path) -> tuple[bool, str]:
    rel = path.as_posix()
    if "/textures/gui/" in rel:
        return True, "gui-exception"
    if rel.endswith(".mcmeta"):
        return True, "metadata"
    return False, ""


def upscale_image(path: Path, target: int, dry_run: bool = False) -> tuple[bool, str]:
    ex, reason = is_exception(path)
    if ex:
        return False, reason

    with Image.open(path) as img:
        w, h = img.size
        if w == 0 or h == 0:
            return False, "invalid-size"
        if w == target and (h % target == 0):
            return False, "already-512"

        scale = target / w
        new_size = (target, max(1, int(round(h * scale))))
        if dry_run:
            return True, f"dry-run {w}x{h}->{new_size[0]}x{new_size[1]}"

        up = img.resize(new_size, Image.Resampling.LANCZOS)
        # Mild denoise + unsharp to avoid blur/ringing.
        up = up.filter(ImageFilter.GaussianBlur(radius=0.2))
        up = up.filter(ImageFilter.UnsharpMask(radius=1.2, percent=90, threshold=2))
        up.save(path)
        return True, f"{w}x{h}->{new_size[0]}x{new_size[1]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Upscale block/item textures to 512 width.")
    parser.add_argument("--target", type=int, default=512)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    processed = 0
    changed = 0
    for directory in TARGET_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*.png"):
            processed += 1
            did_change, _ = upscale_image(path, args.target, args.dry_run)
            if did_change:
                changed += 1

    print(f"Processed {processed} textures, changed {changed}, target={args.target}")


if __name__ == "__main__":
    main()
