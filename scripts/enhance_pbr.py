#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TEXTURE_ROOT = Path("assets/minecraft/textures")
THEME_PATH = Path("theme.json")
HERO_LIST_PATH = Path("scripts/hero_blocks.txt")
HERO_ITEMS_PATH = Path("scripts/hero_items.txt")

PRIORITY_KEYWORDS = [
    "stone", "cobble", "deepslate", "dirt", "grass", "log", "planks", "wood", "stripped",
    "iron", "gold", "copper", "glass", "ice", "water", "ore", "redstone",
    "ingot", "sword", "pickaxe", "axe", "shovel", "helmet", "chestplate", "leggings", "boots"
]

EMISSIVE_KEYWORDS = [
    "redstone", "sea_lantern", "shroomlight", "magma", "torch", "lantern",
    "soul", "end_rod", "sculk", "ore", "amethyst", "respawn_anchor", "comparator", "repeater"
]

METAL_ITEM_KEYWORDS = [
    "iron", "gold", "copper", "netherite", "chainmail", "sword", "pickaxe", "axe", "shovel", "hoe", "helmet", "chestplate", "leggings", "boots"
]
GEM_ITEM_KEYWORDS = ["diamond", "emerald", "amethyst"]
GLASSY_ITEM_KEYWORDS = ["bottle", "clock", "compass", "crystal"]


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


def load_name_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


def classify_material(name: str, is_item: bool) -> tuple[float, float, float]:
    lname = name.lower()
    if any(k in lname for k in ["iron", "gold", "copper", "netherite"]):
        return (0.19, 0.95, 0.24) if is_item else (0.24, 0.90, 0.28)
    if any(k in lname for k in ["glass", "ice", "water"]):
        return (0.08, 0.00, 0.10)
    if any(k in lname for k in ["stone", "deepslate", "cobble", "ore"]):
        return (0.76, 0.06, 0.42)
    if any(k in lname for k in ["dirt", "grass", "mud"]):
        return (0.86, 0.00, 0.40)
    if any(k in lname for k in ["wood", "log", "planks", "stripped"]):
        return (0.68, 0.00, 0.26)
    if is_item and any(k in lname for k in GEM_ITEM_KEYWORDS):
        return (0.26, 0.15, 0.18)
    return 0.62, 0.00, 0.22


def detail_noise(np, shape: tuple[int, int], freq: float, layers: int = 2) -> "np.ndarray":
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    acc = np.zeros((h, w), dtype=np.float32)
    weight_sum = 0.0
    for i in range(max(1, layers)):
        f = freq * (1.0 + i * 0.55)
        wgt = 1.0 / (1.0 + i * 0.8)
        n = (
            np.sin(2 * np.pi * x / w * f)
            + np.cos(2 * np.pi * y / h * (f - 1))
            + np.sin(2 * np.pi * (x + y) / max(w, h) * (f * 0.7))
        )
        acc += n * wgt
        weight_sum += wgt
    n = acc / max(weight_sum, 1e-8)
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
    return mask.astype(np.float32) * strength


def anisotropic_brush(np, shape: tuple[int, int], anisotropy: float, angle_deg: float = 23.0) -> "np.ndarray":
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    a = np.deg2rad(angle_deg)
    u = x * np.cos(a) + y * np.sin(a)
    v = -x * np.sin(a) + y * np.cos(a)
    stripes = np.sin(2 * np.pi * u / max(16, w // 8)) * 0.5 + 0.5
    long_grad = np.sin(2 * np.pi * v / max(64, h)) * 0.5 + 0.5
    out = stripes * (0.35 + 0.65 * long_grad)
    return np.clip(out * anisotropy, 0, 1)


def item_reflection_boost(name: str, cfg: dict) -> tuple[float, float, float]:
    lname = name.lower()
    m = float(cfg.get("metal_item_boost", 1.35))
    g = float(cfg.get("gem_item_boost", 1.2))
    gl = float(cfg.get("glass_item_boost", 1.15))
    if any(k in lname for k in METAL_ITEM_KEYWORDS):
        return m, 0.92, 0.90
    if any(k in lname for k in GEM_ITEM_KEYWORDS):
        return g, 0.35, 0.25
    if any(k in lname for k in GLASSY_ITEM_KEYWORDS):
        return gl, 0.20, 0.05
    return 1.0, 0.0, 0.0


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


def enhance_for_texture(base_path: Path, emissive_level: int, theme: dict, only_blocks: bool, force_item_reflective: bool) -> None:
    np, Image, ImageFilter, ImageOps = _require_image_libs()

    name = base_path.stem
    if name.endswith(("_n", "_s", "_e")):
        return
    rel = base_path.as_posix()
    is_item = "/item/" in rel
    if only_blocks and "/block/" not in rel:
        return

    pbr_cfg = theme.get("pbr", {})
    micro_cfg = theme.get("microdetail", {})
    item_cfg = theme.get("item_reflectance", {})

    normal_strength = float(pbr_cfg.get("normal_strength", 3.4))
    rough_contrast = float(pbr_cfg.get("roughness_contrast", 1.2))
    ao_strength_cfg = float(pbr_cfg.get("ao_strength", 0.4))
    height_contrast = float(pbr_cfg.get("height_contrast", 1.2))

    freq = float(micro_cfg.get("frequency", 9))
    amp = float(micro_cfg.get("amplitude", 88))
    edge_wear = float(micro_cfg.get("edge_wear", 0.5))
    circuit_strength = float(micro_cfg.get("circuit_line_strength", 0.35))
    sigil_density = float(micro_cfg.get("sigil_density", 0.3))
    layer_count = int(micro_cfg.get("layer_count", 2))
    brush_strength = float(micro_cfg.get("anisotropic_brush_strength", 0.45))
    anisotropy = float(item_cfg.get("anisotropy", 0.6))
    clearcoat = float(item_cfg.get("clearcoat_strength", 0.35))

    with Image.open(base_path) as src:
        img = src.convert("RGBA")
    arr = np.array(img)
    rgb, alpha = arr[..., :3], arr[..., 3]
    gray = np.array(ImageOps.grayscale(img))

    local_boost = 1.45 if "/block/" in rel else 1.12
    roughness, metalness, ao_strength = classify_material(name, is_item=is_item)

    noise = detail_noise(np, gray.shape, freq=freq, layers=layer_count)
    edges = edge_map(np, gray)
    sigils = sigil_lines(np, gray.shape, density=sigil_density, strength=circuit_strength)
    brush = anisotropic_brush(np, gray.shape, anisotropy=anisotropy)

    height_f = (
        gray.astype(np.float32) * (0.62 * height_contrast)
        + noise * amp * local_boost
        + edges * (78 * edge_wear) * local_boost
        + sigils * 44.0
        + brush * (20.0 if is_item else 8.0)
    )
    height = np.clip(height_f, 0, 255).astype(np.uint8)

    ao = np.clip(255 - (255 - gray) * (max(0.1, ao_strength + ao_strength_cfg)), 0, 255).astype(np.uint8)
    n_rgba = simple_normal_from_height(np, height, strength=normal_strength * local_boost)
    n_rgba[..., 3] = alpha
    Image.fromarray(n_rgba, mode="RGBA").save(base_path.with_name(f"{name}_n.png"))

    jitter = (noise * (39 * rough_contrast) - (19 * rough_contrast)) * local_boost
    g = np.full_like(gray, int(roughness * 255), dtype=np.float32) + jitter + edges * 14 + sigils * 18
    b = np.full_like(gray, int(metalness * 255), dtype=np.float32)

    if is_item:
        mul, item_metalness, item_gloss = item_reflection_boost(name, item_cfg)
        if force_item_reflective or mul > 1.0:
            g = g * (1.0 - 0.20 * mul) - (brush * (42 * item_gloss + clearcoat * 40))
            b = np.maximum(b, 255 * item_metalness)
            g = g - edges * (12 * mul)

    g = np.clip(g, 0, 255).astype(np.uint8)
    b = np.clip(b, 0, 255).astype(np.uint8)

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
    parser.add_argument("--hero-items", default=str(HERO_ITEMS_PATH))
    parser.add_argument("--phase", choices=["hero", "all"], default="hero")
    parser.add_argument("--emissive-level", type=int, choices=[1, 2, 3, 4, 5], default=4)
    parser.add_argument("--include-items", action="store_true")
    parser.add_argument("--force-item-reflective", action="store_true", help="强制全部 item 走高反光路径")
    args = parser.parse_args()

    theme = load_theme(Path(args.theme))
    hero_blocks = load_name_set(Path(args.hero_list))
    hero_items = load_name_set(Path(args.hero_items))
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
            if stem in hero_blocks or (args.include_items and stem in hero_items):
                targets.append(p)
        else:
            if any(k in stem for k in PRIORITY_KEYWORDS):
                targets.append(p)

    for path in targets:
        enhance_for_texture(
            path,
            emissive_level=args.emissive_level,
            theme=theme,
            only_blocks=only_blocks,
            force_item_reflective=args.force_item_reflective,
        )

    print(
        f"Enhanced {len(targets)} textures "
        f"(phase={args.phase}, include_items={args.include_items}, reflective={args.force_item_reflective})."
    )


if __name__ == "__main__":
    main()
