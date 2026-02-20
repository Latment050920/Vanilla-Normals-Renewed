#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageOps

TEXTURE_ROOT = Path("assets/minecraft/textures")

PRIORITY_KEYWORDS = [
    "stone", "cobble", "deepslate", "dirt", "grass", "log", "planks", "wood", "stripped",
    "iron", "gold", "copper", "glass", "ice", "water", "ore", "redstone"
]

EMISSIVE_KEYWORDS = [
    "redstone", "glow", "sea_lantern", "shroomlight", "magma", "torch", "lantern",
    "soul", "end_rod", "end_stone", "sculk", "ore", "amethyst", "respawn_anchor"
]


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as i:
        return i.convert("RGBA")


def simple_normal_from_height(gray: np.ndarray, strength: float = 2.5) -> np.ndarray:
    h = gray.astype(np.float32) / 255.0
    dx = np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)
    dy = np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    out = np.stack([
        ((nx * 0.5 + 0.5) * 255),
        ((ny * 0.5 + 0.5) * 255),
        ((nz * 0.5 + 0.5) * 255),
        np.full_like(nx, 255),
    ], axis=-1)
    return out.astype(np.uint8)


def detail_noise(shape: tuple[int, int], seed: int = 13) -> np.ndarray:
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    # Tileable trigonometric micro-detail.
    n = (
        np.sin(2 * np.pi * x / w * 8.0)
        + np.cos(2 * np.pi * y / h * 7.0)
        + np.sin(2 * np.pi * (x + y) / max(w, h) * 5.0)
    )
    n = (n - n.min()) / (n.max() - n.min() + 1e-8)
    return n


def classify_material(name: str) -> tuple[float, float, float]:
    # roughness, metalness, ao_strength
    lname = name.lower()
    if any(k in lname for k in ["iron", "gold", "copper", "netherite"]):
        return 0.30, 0.80, 0.25
    if any(k in lname for k in ["glass", "ice", "water"]):
        return 0.08, 0.00, 0.10
    if any(k in lname for k in ["stone", "deepslate", "cobble", "ore"]):
        return 0.72, 0.05, 0.35
    if any(k in lname for k in ["dirt", "grass", "mud"]):
        return 0.82, 0.00, 0.35
    if any(k in lname for k in ["wood", "log", "planks", "stripped"]):
        return 0.66, 0.00, 0.20
    return 0.60, 0.00, 0.20


def enhance_for_texture(base_path: Path, emissive_level: int) -> None:
    name = base_path.stem
    if name.endswith(("_n", "_s", "_e")):
        return

    img = load_rgba(base_path)
    arr = np.array(img)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    gray = np.array(ImageOps.grayscale(img))

    noise = detail_noise(gray.shape)
    roughness, metalness, ao_strength = classify_material(name)

    # Height and AO proxies from luminance + micro-noise.
    height = np.clip(gray.astype(np.float32) * 0.75 + noise * 64.0, 0, 255).astype(np.uint8)
    ao = np.clip(255 - (255 - gray) * ao_strength, 0, 255).astype(np.uint8)

    # _n map.
    n_rgba = simple_normal_from_height(height, strength=2.3)
    n_rgba[..., 3] = alpha
    Image.fromarray(n_rgba, mode="RGBA").save(base_path.with_name(f"{name}_n.png"))

    # _s LabPBR-ish payload:
    # R=AO, G=roughness, B=metalness, A=height
    g = np.clip(np.full_like(gray, int(roughness * 255)) + (noise * 20 - 10), 0, 255).astype(np.uint8)
    b = np.full_like(gray, int(metalness * 255), dtype=np.uint8)
    s = np.stack([ao, g, b, height], axis=-1)
    s[..., 3] = np.maximum(s[..., 3], alpha)
    Image.fromarray(s.astype(np.uint8), mode="RGBA").save(base_path.with_name(f"{name}_s.png"))

    if any(k in name.lower() for k in EMISSIVE_KEYWORDS):
        lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])
        threshold = 140 - emissive_level * 10
        mask = np.clip((lum - threshold) / max(1, (255 - threshold)), 0, 1)
        # edge-preserving blur reduction
        glow = (mask * (40 + emissive_level * 40)).astype(np.uint8)
        e = np.zeros_like(arr)
        e[..., :3] = np.stack([glow, glow, glow], axis=-1)
        e[..., 3] = alpha
        e_img = Image.fromarray(e, mode="RGBA").filter(ImageFilter.GaussianBlur(radius=0.35))
        e_img.save(base_path.with_name(f"{name}_e.png"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance/generate PBR maps and emissives.")
    parser.add_argument("--emissive-level", type=int, default=3, choices=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    targets = []
    for p in TEXTURE_ROOT.rglob("*.png"):
        if "/block/" not in p.as_posix() and "/item/" not in p.as_posix():
            continue
        stem = p.stem.lower()
        if stem.endswith(("_n", "_s", "_e")):
            continue
        if any(k in stem for k in PRIORITY_KEYWORDS):
            targets.append(p)

    for path in targets:
        enhance_for_texture(path, emissive_level=args.emissive_level)

    print(f"Enhanced PBR for {len(targets)} priority textures.")


if __name__ == "__main__":
    main()
