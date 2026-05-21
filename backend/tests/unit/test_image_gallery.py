"""Unit tests for image gallery helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.services.image_gallery import (
    image_dimensions,
    iter_readable_images,
    load_labels_map,
    save_labels_map,
    stable_image_id,
)


def test_image_dimensions_valid_jpeg(tmp_path: Path) -> None:
    path = tmp_path / "ok.jpg"
    Image.new("RGB", (32, 24), color=(1, 2, 3)).save(path)
    assert image_dimensions(path) == (32, 24)


def test_image_dimensions_invalid_file_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "not_image.txt"
    path.write_text("not an image", encoding="utf-8")
    assert image_dimensions(path) is None


def test_iter_readable_images_skips_invalid(tmp_path: Path) -> None:
    Image.new("RGB", (10, 10)).save(tmp_path / "good.png")
    (tmp_path / "bad.bin").write_bytes(b"\x00\x01")
    readable = iter_readable_images(str(tmp_path))
    assert len(readable) == 1
    assert readable[0][0].name == "good.png"
    assert readable[0][1:] == (10, 10)


def test_labels_json_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "gallery"
    root.mkdir()
    save_labels_map(str(root), {"a.jpg": ["cat"]})
    assert load_labels_map(str(root)) == {"a.jpg": ["cat"]}


def test_stable_image_id_deterministic() -> None:
    import uuid

    pid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    did = uuid.UUID("22222222-2222-2222-2222-222222222222")
    a = stable_image_id(pid, did, "x.jpg")
    b = stable_image_id(pid, did, "x.jpg")
    assert a == b
