#!/usr/bin/env python3
"""
DeepFlow synthetic dataset generator (P9 DevOps).

Fast tabular CSV + tiny vision fixtures for backend integration / smoke tests.
Uses stdlib + Pillow (project dependency); no numpy required.

Usage:
    python scripts/gen_synthetic_data.py
    python scripts/gen_synthetic_data.py --tabular-rows 200 --vision-images 40
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABULAR_DIR = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_data" / "tabular"
DEFAULT_VISION_DIR = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_data" / "vision"

TABULAR_COLUMNS = [
    "age",
    "blood_pressure",
    "bmi",
    "glucose",
    "heart_rate",
    "cholesterol",
    "risk_label",
]


def generate_tabular_csv(
    output_dir: Path,
    *,
    rows: int = 100,
    filename: str = "health_metrics.csv",
    seed: int = 42,
) -> Path:
    """
    Generate a tabular CSV with physiological features and binary risk_label.

    Columns: age, blood_pressure, bmi, glucose, heart_rate, cholesterol, risk_label (0|1).
    """
    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=TABULAR_COLUMNS)
        writer.writeheader()
        for _ in range(rows):
            age = rng.randint(18, 85)
            blood_pressure = rng.randint(90, 180)
            bmi = round(rng.uniform(15.0, 40.0), 1)
            glucose = rng.randint(70, 200)
            heart_rate = rng.randint(55, 110)
            cholesterol = rng.randint(120, 280)

            # Simple rule-based label for plausible synthetic data
            risk_score = 0
            if age >= 55:
                risk_score += 1
            if blood_pressure >= 140:
                risk_score += 1
            if bmi >= 30.0:
                risk_score += 1
            if glucose >= 140:
                risk_score += 1
            if heart_rate >= 95:
                risk_score += 1
            risk_label = 1 if risk_score >= 2 or rng.random() < 0.15 else 0

            writer.writerow(
                {
                    "age": age,
                    "blood_pressure": blood_pressure,
                    "bmi": bmi,
                    "glucose": glucose,
                    "heart_rate": heart_rate,
                    "cholesterol": cholesterol,
                    "risk_label": risk_label,
                }
            )

    return out_path


def generate_vision_dataset(
    output_dir: Path,
    *,
    num_images: int = 20,
    image_size: int = 32,
    num_classes: int = 5,
    seed: int = 42,
    labels_filename: str = "labels.csv",
) -> tuple[Path, Path]:
    """
    Generate tiny RGB images and a labels.csv (filename, label).

    Labels are integers 0 .. num_classes-1 (default 0-4).
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for vision fixtures. Install with:\n"
            "  pip install Pillow\n"
            "or: pip install -r requirements.txt"
        ) from exc

    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_path = output_dir / labels_filename

    label_rows: list[dict[str, str | int]] = []

    for idx in range(num_images):
        label = idx % num_classes
        filename = f"img_{idx:04d}.png"
        filepath = output_dir / filename

        # Class-tinted random noise — fast, no numpy
        base_r = int(255 * label / max(1, num_classes - 1))
        pixels = bytearray(image_size * image_size * 3)
        for i in range(0, len(pixels), 3):
            noise = rng.randint(-40, 40)
            pixels[i] = max(0, min(255, base_r + noise))
            pixels[i + 1] = max(0, min(255, rng.randint(60, 200)))
            pixels[i + 2] = max(0, min(255, 255 - base_r + noise))

        Image.frombytes("RGB", (image_size, image_size), bytes(pixels)).save(filepath, format="PNG")
        label_rows.append({"filename": filename, "label": label})

    with labels_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["filename", "label"])
        writer.writeheader()
        writer.writerows(label_rows)

    return output_dir, labels_path


def generate_all(
    tabular_dir: Path = DEFAULT_TABULAR_DIR,
    vision_dir: Path = DEFAULT_VISION_DIR,
    *,
    tabular_rows: int = 100,
    vision_images: int = 20,
    seed: int = 42,
) -> dict[str, str | int]:
    csv_path = generate_tabular_csv(tabular_dir, rows=tabular_rows, seed=seed)
    vision_root, labels_path = generate_vision_dataset(
        vision_dir,
        num_images=vision_images,
        seed=seed + 1,
    )
    return {
        "tabular_csv": str(csv_path),
        "tabular_rows": tabular_rows,
        "vision_dir": str(vision_root),
        "vision_images": vision_images,
        "labels_csv": str(labels_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic tabular + vision fixtures.")
    parser.add_argument("--tabular-dir", type=Path, default=DEFAULT_TABULAR_DIR)
    parser.add_argument("--vision-dir", type=Path, default=DEFAULT_VISION_DIR)
    parser.add_argument("--tabular-rows", type=int, default=100)
    parser.add_argument("--vision-images", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = generate_all(
        args.tabular_dir,
        args.vision_dir,
        tabular_rows=args.tabular_rows,
        vision_images=args.vision_images,
        seed=args.seed,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
