#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

TEXTURE_ROOT = Path("assets/minecraft/textures")

PRIORITY_KEYWORDS = [
    "stone", "cobble", "deepslate", "dirt", "grass", "log", "planks", "wood", "stripped",
    "iron", "gold", "copper", "glass", "ice", "water", "ore", "redstone"
]

EMISSIVE_KEYWORDS = [
    "redstone", "glow", "sea_lantern", "shroomlight", "magma", "torch", "lantern",
    "soul", "end_rod", "end", "sculk", "ore", "amethyst", "respawn_anchor"
]

# 用于“纹理更显眼”的可复现参数档位。
DETAIL_PROFILES: dict[str, dict[str, float]] = {
    "soft": {
        "noise_amp": 40.0,
        "edge_amp": 24.0,
        "normal_strength": 2.2,
        "roughness_jitter": 12.0,
        "emissive_boost": 1.0,
    },
    "balanced": {
        "noise_amp": 64.0,
        "edge_amp": 40.0,
        "normal_strength": 2.8,
        "roughness_jitter": 20.0,
        "emissive_boost": 1.1,
    },
    "bold": {
        "noise_amp": 92.0,
        "edge_amp": 64.0,
        "normal_strength": 3.5,
        "roughness_jitter": 34.0,
        "emissive_boost": 1.25,
    },
}


def _require_image_libs():
    try:
        import numpy as np
        from PIL import Image, ImageFilter, ImageOps
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependencies: please install pillow and numpy before running this script."
        ) from exc
    return np, Image, ImageFilter, ImageOps


def classify_material(name: str) -> tuple[float, float, float]:
    lname = name.lower()
    if any(k in lname for k in ["iron", "gold", "copper", "netherite"]):
        return 0.25, 0.90, 0.28
    if any(k in lname for k in ["glass", "ice", "water"]):
        return 0.08, 0.00, 0.12
    if any(k in lname for k in ["stone", "deepslate", "cobble", "ore"]):
        return 0.76, 0.06, 0.40
    if any(k in lname for k in ["dirt", "grass", "mud"]):
        return 0.85, 0.00, 0.40
    if any(k in lname for k in ["wood", "log", "planks", "stripped"]):
        return 0.68, 0.00, 0.24
    return 0.62, 0.00, 0.22


def detail_noise(np, shape: tuple[int, int]) -> "np.ndarray":
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    n = (
        np.sin(2 * np.pi * x / w * 8.0)
        + np.cos(2 * np.pi * y / h * 7.0)
        + np.sin(2 * np.pi * (x + y) / max(w, h) * 5.0)
    )
    n = (n - n.min()) / (n.max() - n.min() + 1e-8)
    return n


def edge_map(np, gray: "np.ndarray") -> "np.ndarray":
    gx = np.roll(gray, -1, axis=1).astype(np.float32) - np.roll(gray, 1, axis=1).astype(np.float32)
    gy = np.roll(gray, -1, axis=0).astype(np.float32) - np.roll(gray, 1, axis=0).astype(np.float32)
    g = np.sqrt(gx * gx + gy * gy)
    g = g / (g.max() + 1e-8)
    return g


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


def enhance_for_texture(base_path: Path, emissive_level: int, profile: dict[str, float], detail_boost: float, only_blocks: bool) -> None:
    np, Image, ImageFilter, ImageOps = _require_image_libs()

    name = base_path.stem
    if name.endswith(("_n", "_s", "_e")):
        return
    if only_blocks and "/block/" not in base_path.as_posix():
        return

    with Image.open(base_path) as src:
        img = src.convert("RGBA")
    arr = np.array(img)
    rgb, alpha = arr[..., :3], arr[..., 3]
    gray = np.array(ImageOps.grayscale(img))

    # 方块比物品更突出：默认额外加强细节。
    local_boost = detail_boost * (1.35 if "/block/" in base_path.as_posix() else 1.0)

    roughness, metalness, ao_strength = classify_material(name)
    noise = detail_noise(np, gray.shape)
    edges = edge_map(np, gray)

    height_f = (
        gray.astype(np.float32) * 0.65
        + noise * profile["noise_amp"] * local_boost
        + edges * profile["edge_amp"] * local_boost
    )
    height = np.clip(height_f, 0, 255).astype(np.uint8)
    ao = np.clip(255 - (255 - gray) * (ao_strength * (0.9 + 0.2 * local_boost)), 0, 255).astype(np.uint8)

    n_rgba = simple_normal_from_height(np, height, strength=profile["normal_strength"] * local_boost)
    n_rgba[..., 3] = alpha
    Image.fromarray(n_rgba, mode="RGBA").save(base_path.with_name(f"{name}_n.png"))

    jitter = (noise * profile["roughness_jitter"] - profile["roughness_jitter"] / 2.0) * local_boost
    g = np.clip(np.full_like(gray, int(roughness * 255), dtype=np.float32) + jitter + edges * 8, 0, 255).astype(np.uint8)
    b = np.full_like(gray, int(metalness * 255), dtype=np.uint8)
    s = np.stack([ao, g, b, height], axis=-1)
    s[..., 3] = np.maximum(s[..., 3], alpha)
    Image.fromarray(s.astype(np.uint8), mode="RGBA").save(base_path.with_name(f"{name}_s.png"))

    if any(k in name.lower() for k in EMISSIVE_KEYWORDS):
        lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        threshold = 150 - emissive_level * 12
        mask = np.clip((lum - threshold) / max(1, (255 - threshold)), 0, 1)
        glow = (mask * (30 + emissive_level * 38) * profile["emissive_boost"]).astype(np.uint8)
        e = np.zeros_like(arr)
        e[..., :3] = np.stack([glow, glow, glow], axis=-1)
        e[..., 3] = alpha
        e_img = Image.fromarray(e, mode="RGBA").filter(ImageFilter.GaussianBlur(radius=0.30))
        e_img.save(base_path.with_name(f"{name}_e.png"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance/generate PBR maps and emissives.")
    parser.add_argument("--emissive-level", type=int, default=3, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--detail-profile", choices=sorted(DETAIL_PROFILES), default="bold", help="纹理细节强度档位")
    parser.add_argument("--detail-boost", type=float, default=1.0, help="额外细节倍率，建议 0.8~1.6")
    parser.add_argument("--only-blocks", action="store_true", default=True, help="仅处理方块纹理（默认 true）")
    parser.add_argument("--include-items", action="store_true", help="包含 item 纹理")
    args = parser.parse_args()

    only_blocks = args.only_blocks and not args.include_items
    profile = DETAIL_PROFILES[args.detail_profile]

    targets = []
    for p in TEXTURE_ROOT.rglob("*.png"):
        rel = p.as_posix()
        if "/block/" not in rel and "/item/" not in rel:
            continue
        stem = p.stem.lower()
        if stem.endswith(("_n", "_s", "_e")):
            continue
        if any(k in stem for k in PRIORITY_KEYWORDS):
            targets.append(p)

    for path in targets:
        enhance_for_texture(
            path,
            emissive_level=args.emissive_level,
            profile=profile,
            detail_boost=args.detail_boost,
            only_blocks=only_blocks,
        )

    scope = "block-only" if only_blocks else "block+item"
    print(f"Enhanced PBR for {len(targets)} priority textures (profile={args.detail_profile}, scope={scope}).")


if __name__ == "__main__":
    main()
