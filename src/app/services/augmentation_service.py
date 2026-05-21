"""CV data augmentation — Pillow-based image transforms."""

from __future__ import annotations

import random
import uuid
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.errors import ERR_DATASET_INVALID_PARAM, AppError
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.eda import AugmentRequest
from shared.protocols import StorageProtocol

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def _list_image_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES:
        return [path]
    if path.is_dir():
        return sorted(
            p for p in path.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES
        )
    return []


def _apply_transform(img: Image.Image, transform_type: str, params: dict) -> Image.Image:
    if transform_type == "rotate":
        angle = float(params.get("angle", 15))
        return img.rotate(angle, expand=True)
    if transform_type == "flip_horizontal":
        return ImageOps.mirror(img)
    if transform_type == "flip_vertical":
        return ImageOps.flip(img)
    if transform_type == "color_jitter":
        brightness = float(params.get("brightness", 0.2))
        contrast = float(params.get("contrast", 0.2))
        out = ImageEnhance.Brightness(img).enhance(1.0 + random.uniform(-brightness, brightness))
        return ImageEnhance.Contrast(out).enhance(1.0 + random.uniform(-contrast, contrast))
    if transform_type == "random_crop":
        w, h = img.size
        ratio = float(params.get("ratio", 0.8))
        cw, ch = max(1, int(w * ratio)), max(1, int(h * ratio))
        left = random.randint(0, max(0, w - cw))
        top = random.randint(0, max(0, h - ch))
        cropped = img.crop((left, top, left + cw, top + ch))
        return cropped.resize((w, h))
    if transform_type == "gaussian_blur":
        radius = float(params.get("radius", 2))
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    if transform_type in ("mixup", "cutmix"):
        # Day2: treat as mild color blend placeholder when single image
        return ImageEnhance.Brightness(img).enhance(1.1)
    raise AppError.bad_request(f"Unsupported transform: {transform_type}", code=ERR_DATASET_INVALID_PARAM)


class PillowAugmentationService:
    def __init__(self, repo: DatasetRepository, storage: StorageProtocol) -> None:
        self._repo = repo
        self._storage = storage

    def augment(self, project_id: uuid.UUID, dataset_id: uuid.UUID, body: AugmentRequest) -> dict:
        source = self._repo.get_by_id_and_project(dataset_id, project_id)
        if not source:
            raise AppError.not_found("Dataset not found")

        fmt_value = source.format.value if hasattr(source.format, "value") else str(source.format)
        if fmt_value != "image":
            raise AppError.bad_request(
                "Augmentation requires an image dataset",
                code=ERR_DATASET_INVALID_PARAM,
            )
        if not source.file_path:
            raise AppError.bad_request("Dataset path is missing", code=ERR_DATASET_INVALID_PARAM)

        images = _list_image_files(Path(source.file_path))
        if not images:
            raise AppError.bad_request("No images found in dataset path", code=ERR_DATASET_INVALID_PARAM)
        if not body.transforms:
            raise AppError.bad_request("At least one transform is required", code=ERR_DATASET_INVALID_PARAM)

        new_id = uuid.uuid4()
        out_dir = Path(self._storage.get_raw_path(str(project_id), str(new_id)))
        out_dir.mkdir(parents=True, exist_ok=True)

        augmented_count = 0
        for img_path in images:
            with Image.open(img_path) as base:
                base = base.convert("RGB")
                dest = out_dir / img_path.name
                base.save(dest)

                for aug_idx in range(body.num_augmented):
                    current = base.copy()
                    for t in body.transforms:
                        current = _apply_transform(current, t.type, t.params)
                    aug_name = f"{img_path.stem}_aug{aug_idx}{img_path.suffix}"
                    current.save(out_dir / aug_name)
                    augmented_count += 1

        output_name = body.output_dataset_name or f"{source.name}_aug"
        row = self._repo.create(
            dataset_id=new_id,
            project_id=project_id,
            name=output_name,
            format="image",
            file_path=str(out_dir),
            num_samples=len(images) + augmented_count,
            columns_meta=source.columns_meta,
            tags=list(source.tags or []) + ["augmented"],
            status="ready",
        )

        return {
            "original_count": len(images),
            "augmented_count": augmented_count,
            "new_dataset_id": str(row.id),
            "output_dataset_name": output_name,
        }
