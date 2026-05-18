#!/usr/bin/env python3
"""
DeepFlow synthetic dataset generator.

Produces tabular CSV and random classification images for fast training smoke tests
(target: complete one epoch in ~5 seconds on a small CNN).

Usage:
    python scripts/gen_synthetic_data.py --output ./data/synthetic
    python scripts/gen_synthetic_data.py -o ./data/synthetic --preset fast-epoch
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

PRESETS = {
    "fast-epoch": {
        "csv_rows": 200,
        "images": 60,
        "image_size": 32,
        "num_classes": 3,
        "images_per_class": 20,
    },
    "default": {
        "csv_rows": 500,
        "images": 150,
        "image_size": 64,
        "num_classes": 5,
        "images_per_class": 30,
    },
}


def _write_csv(path: Path, rows: int, seed: int) -> dict[str, int | str]:
    rng = random.Random(seed)
    columns = ["id", "feature_a", "feature_b", "category", "label"]
    path.parent.mkdir(parents=True, exist_ok=True)

    categories = ["A", "B", "C"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for i in range(rows):
            cat = categories[i % len(categories)]
            writer.writerow(
                {
                    "id": i,
                    "feature_a": round(rng.uniform(0, 1), 6),
                    "feature_b": round(rng.gauss(0.5, 0.15), 6),
                    "category": cat,
                    "label": categories.index(cat),
                }
            )
    return {"path": str(path), "rows": rows, "columns": len(columns)}


def _write_images(
    root: Path,
    *,
    num_classes: int,
    images_per_class: int,
    image_size: int,
    seed: int,
) -> dict[str, int | str]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for image generation. Install with:\n"
            "  pip install -r scripts/requirements-synthetic.txt"
        ) from exc

    rng = random.Random(seed)
    root.mkdir(parents=True, exist_ok=True)
    total = 0

    for class_idx in range(num_classes):
        class_dir = root / f"class_{class_idx}"
        class_dir.mkdir(parents=True, exist_ok=True)
        hue = int(255 * class_idx / max(1, num_classes))

        for img_idx in range(images_per_class):
            pixels = bytearray(image_size * image_size * 3)
            for i in range(0, len(pixels), 3):
                noise = rng.randint(-30, 30)
                pixels[i] = max(0, min(255, hue + noise))
                pixels[i + 1] = max(0, min(255, 128 + noise))
                pixels[i + 2] = max(0, min(255, 255 - hue + noise))

            img = Image.frombytes("RGB", (image_size, image_size), bytes(pixels))
            img.save(class_dir / f"img_{img_idx:04d}.jpg", format="JPEG", quality=85)
            total += 1

    return {
        "path": str(root),
        "images": total,
        "num_classes": num_classes,
        "image_size": image_size,
    }


def generate_dataset(
    output_dir: Path,
    *,
    csv_rows: int,
    images: int,
    image_size: int,
    num_classes: int,
    images_per_class: int | None,
    seed: int,
) -> dict:
    if images_per_class is None:
        images_per_class = max(1, images // max(1, num_classes))

    t0 = time.perf_counter()
    csv_info = _write_csv(output_dir / "tabular" / "synthetic.csv", csv_rows, seed)
    image_info = _write_images(
        output_dir / "images",
        num_classes=num_classes,
        images_per_class=images_per_class,
        image_size=image_size,
        seed=seed + 1,
    )

    meta = {
        "generator": "gen_synthetic_data.py",
        "seed": seed,
        "csv": csv_info,
        "images": image_info,
        "elapsed_sec": round(time.perf_counter() - t0, 3),
    }
    meta_path = output_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["meta_path"] = str(meta_path)
    return meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic CSV + image data.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/synthetic"),
        help="Output directory (default: data/synthetic)",
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), default=None)
    parser.add_argument("--csv-rows", type=int, default=None)
    parser.add_argument("--images", type=int, default=None, help="Total images (approx.)")
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--num-classes", type=int, default=None)
    parser.add_argument("--images-per-class", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = dict(PRESETS["default"])
    if args.preset:
        cfg.update(PRESETS[args.preset])

    for attr in ("csv_rows", "images", "image_size", "num_classes", "images_per_class"):
        val = getattr(args, attr, None)
        if val is not None:
            cfg[attr] = val

    meta = generate_dataset(
        args.output.resolve(),
        csv_rows=cfg["csv_rows"],
        images=cfg["images"],
        image_size=cfg["image_size"],
        num_classes=cfg["num_classes"],
        images_per_class=cfg.get("images_per_class"),
        seed=args.seed,
    )
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
