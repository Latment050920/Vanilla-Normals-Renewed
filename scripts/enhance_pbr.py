#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TEXTURE_ROOT = Path("assets/minecraft/textures")
THEME_PATH = Path("theme.json")
HERO_LIST_PATH = Path("scripts/hero_blocks.txt")

PRIORITY_KEYWORDS = [
    "stone", "cobble", "deepslate", "dirt", "grass", "log", "planks", "wood", "stripped",
    "iron", "gold", "copper", "glass", "ice", "water", "ore", "redstone"
]

EMISSIVE_KEYWORDS = [
    "redstone", "sea_lantern", "shroomlight", "magma", "torch", "lantern",
    "soul", "end_rod", "sculk", "ore", "amethyst", "respawn_anchor", "comparator", "repeater"
]


def _require_image_libs():
    try:
        import numpy as np
        from PIL import Image, ImageFilter, ImageOps
    except Exception as exc:  # pragma: no cover
        raise SystemExit("Missing dependencies: install pillow + numpy.") from exc
    return np, Image, ImageFilter, ImageOps


def load_theme(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_hero_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


def classify_material(name: str) -> tuple[float, float, float]:
    lname = name.lower()
    if any(k in lname for k in ["iron", "gold", "copper", "netherite"]):
        return 0.25, 0.90, 0.28
    if any(k in lname for k in ["glass", "ice", "water"]):
        return 0.10, 0.00, 0.10
    if any(k in lname for k in ["stone", "deepslate", "cobble", "ore"]):
        return 0.76, 0.06, 0.42
    if any(k in lname for k in ["dirt", "grass", "mud"]):
        return 0.86, 0.00, 0.40
    if any(k in lname for k in ["wood", "log", "planks", "stripped"]):
        return 0.68, 0.00, 0.26
    return 0.62, 0.00, 0.22


def detail_noise(np, shape: tuple[int, int], freq: float) -> "np.ndarray":
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    n = (
        np.sin(2 * np.pi * x / w * freq)
        + np.cos(2 * np.pi * y / h * (freq - 1))
        + np.sin(2 * np.pi * (x + y) / max(w, h) * (freq * 0.7))
    )
    n = (n - n.min()) / (n.max() - n.min() + 1e-8)
    return n


def edge_map(np, gray: "np.ndarray") -> "np.ndarray":
    gx = np.roll(gray, -1, axis=1).astype(np.float32) - np.roll(gray, 1, axis=1).astype(np.float32)
    gy = np.roll(gray, -1, axis=0).astype(np.float32) - np.roll(gray, 1, axis=0).astype(np.float32)
    g = np.sqrt(gx * gx + gy * gy)
    return g / (g.max() + 1e-8)


def sigil_lines(np, shape: tuple[int, int], density: float, strength: float) -> "np.ndarray":
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    cell = max(8, int(64 * (1.0 - min(density, 0.9))))
    mask = (((x + 2 * y) % cell) < 2) | (((2 * x - y) % cell) < 2) | (((x - y) % (cell * 2)) < 2)
    out = mask.astype(np.float32) * strength
    return out


def simple_normal_from_height(np, height: "np.ndarray", strength: float) -> "np.ndarray":
    h = height.astype(np.float32) / 255.0
    dx = np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)
    dy = np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)
    nx, ny, nz = -dx * strength, -dy * strength, np.ones_like(dx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    return np.stack([
        ((nx * 0.5 + 0.5) * 255),
        ((ny * 0.5 + 0.5) * 255),
        ((nz * 0.5 + 0.5) * 255),
        np.full_like(nx, 255),
    ], axis=-1).astype(np.uint8)


def enhance_for_texture(base_path: Path, emissive_level: int, theme: dict, only_blocks: bool) -> None:
    np, Image, ImageFilter, ImageOps = _require_image_libs()

    name = base_path.stem
    if name.endswith(("_n", "_s", "_e")):
        return
    rel = base_path.as_posix()
    if only_blocks and "/block/" not in rel:
        return

    pbr_cfg = theme.get("pbr", {})
    micro_cfg = theme.get("microdetail", {})

    normal_strength = float(pbr_cfg.get("normal_strength", 3.4))
    rough_contrast = float(pbr_cfg.get("roughness_contrast", 1.2))
    ao_strength_cfg = float(pbr_cfg.get("ao_strength", 0.4))
    height_contrast = float(pbr_cfg.get("height_contrast", 1.2))

    freq = float(micro_cfg.get("frequency", 9))
    amp = float(micro_cfg.get("amplitude", 88))
    edge_wear = float(micro_cfg.get("edge_wear", 0.5))
    circuit_strength = float(micro_cfg.get("circuit_line_strength", 0.35))
    sigil_density = float(micro_cfg.get("sigil_density", 0.3))

    with Image.open(base_path) as src:
        img = src.convert("RGBA")
    arr = np.array(img)
    rgb, alpha = arr[..., :3], arr[..., 3]
    gray = np.array(ImageOps.grayscale(img))

    local_boost = 1.4 if "/block/" in rel else 1.0
    roughness, metalness, ao_strength = classify_material(name)

    noise = detail_noise(np, gray.shape, freq=freq)
    edges = edge_map(np, gray)
    sigils = sigil_lines(np, gray.shape, density=sigil_density, strength=circuit_strength)

    height_f = (
        gray.astype(np.float32) * (0.62 * height_contrast)
        + noise * amp * local_boost
        + edges * (70 * edge_wear) * local_boost
        + sigils * 40.0
    )
    height = np.clip(height_f, 0, 255).astype(np.uint8)

    ao = np.clip(255 - (255 - gray) * (max(0.1, ao_strength + ao_strength_cfg)), 0, 255).astype(np.uint8)
    n_rgba = simple_normal_from_height(np, height, strength=normal_strength * local_boost)
    n_rgba[..., 3] = alpha
    Image.fromarray(n_rgba, mode="RGBA").save(base_path.with_name(f"{name}_n.png"))

    jitter = (noise * (35 * rough_contrast) - (17 * rough_contrast)) * local_boost
    g = np.clip(np.full_like(gray, int(roughness * 255), dtype=np.float32) + jitter + edges * 12 + sigils * 16, 0, 255).astype(np.uint8)
    b = np.full_like(gray, int(metalness * 255), dtype=np.uint8)
    s = np.stack([ao, g, b, height], axis=-1)
    s[..., 3] = np.maximum(s[..., 3], alpha)
    Image.fromarray(s.astype(np.uint8), mode="RGBA").save(base_path.with_name(f"{name}_s.png"))

    if any(k in name.lower() for k in EMISSIVE_KEYWORDS):
        lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        threshold = 160 - emissive_level * 14
        circuit_mask = np.clip(sigils * 1.8, 0, 1)
        base_mask = np.clip((lum - threshold) / max(1, (255 - threshold)), 0, 1)
        mask = np.clip(base_mask + circuit_mask * 0.75, 0, 1)
        glow = (mask * (26 + emissive_level * 40)).astype(np.uint8)
        e = np.zeros_like(arr)
        e[..., :3] = np.stack([glow, glow, glow], axis=-1)
        e[..., 3] = alpha
        e_img = Image.fromarray(e, mode="RGBA").filter(ImageFilter.GaussianBlur(radius=0.25))
        e_img.save(base_path.with_name(f"{name}_e.png"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance/generate PBR maps and emissives.")
    parser.add_argument("--theme", default=str(THEME_PATH))
    parser.add_argument("--hero-list", default=str(HERO_LIST_PATH))
    parser.add_argument("--phase", choices=["hero", "all"], default="hero")
    parser.add_argument("--emissive-level", type=int, choices=[1, 2, 3, 4, 5], default=4)
    parser.add_argument("--include-items", action="store_true")
    args = parser.parse_args()

    theme = load_theme(Path(args.theme))
    hero_set = load_hero_set(Path(args.hero_list))
    only_blocks = not args.include_items

    targets = []
    for p in TEXTURE_ROOT.rglob("*.png"):
        rel = p.as_posix()
        if "/block/" not in rel and "/item/" not in rel:
            continue
        stem = p.stem.lower()
        if stem.endswith(("_n", "_s", "_e")):
            continue
        if args.phase == "hero":
            if stem in hero_set:
                targets.append(p)
        else:
            if any(k in stem for k in PRIORITY_KEYWORDS):
                targets.append(p)

    for path in targets:
        enhance_for_texture(path, emissive_level=args.emissive_level, theme=theme, only_blocks=only_blocks)

    print(f"Enhanced {len(targets)} textures (phase={args.phase}, include_items={args.include_items}).")


if __name__ == "__main__":
    main()
