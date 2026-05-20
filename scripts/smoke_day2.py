"""Day2 smoke test: upload -> preview -> clean -> EDA -> image augment."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
from PIL import Image

BASE = "http://127.0.0.1:8000/api/v1"
PROJECT = "11111111-1111-1111-1111-111111111111"
CSV = "name,age,score\nAlice,30,88\nBob,,92\nBob,,92\nCharlie,25,70\n"


def ok(resp: httpx.Response, step: str) -> dict:
    if resp.status_code >= 400:
        print(f"FAIL [{step}] HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)
    body = resp.json()
    if body.get("code") != 0:
        print(f"FAIL [{step}] code={body.get('code')} msg={body.get('message')}")
        sys.exit(1)
    return body["data"]


def main() -> None:
    client = httpx.Client(timeout=30.0)

    health = client.get(f"{BASE}/health")
    data = ok(health, "health")
    assert data["db"] == "connected", data
    print("OK health")

    files = {"file": ("day2_test.csv", CSV.encode("utf-8"), "text/csv")}
    form = {"name": "day2_test", "tags": "smoke,day2"}
    upload = client.post(f"{BASE}/projects/{PROJECT}/datasets/upload", files=files, data=form)
    ds = ok(upload, "upload")
    ds_id = ds["id"]
    assert ds["num_samples"] == 4, ds
    assert len(ds["columns_meta"]) == 3, ds
    print(f"OK upload ds_id={ds_id} samples={ds['num_samples']}")

    preview = client.get(f"{BASE}/projects/{PROJECT}/datasets/{ds_id}/preview", params={"limit": 10})
    prev = ok(preview, "preview")
    assert prev["total_rows"] == 4, prev
    assert len(prev["rows"]) >= 1, prev
    assert "name" in prev["columns"], prev
    print(f"OK preview rows={len(prev['rows'])} cols={prev['columns']}")

    clean = client.post(
        f"{BASE}/projects/{PROJECT}/datasets/{ds_id}/clean/missing",
        json={"columns": ["age"], "strategy": "fill_median"},
    )
    result = ok(clean, "clean/missing")
    assert result["rows_before"] == 4, result
    assert result["rows_after"] == 4, result
    new_id = result["dataset_id"]
    print(f"OK clean missing new_ds={new_id} rows_after={result['rows_after']}")

    dedup = client.post(
        f"{BASE}/projects/{PROJECT}/datasets/{ds_id}/clean/dedup",
        json={"keep": "first"},
    )
    ded = ok(dedup, "clean/dedup")
    assert ded["rows_after"] == 3, ded
    print(f"OK dedup rows_after={ded['rows_after']}")

    eda_run = client.post(
        f"{BASE}/projects/{PROJECT}/datasets/{ds_id}/eda",
        json={"include_visualizations": True},
    )
    ok(eda_run, "eda")
    report = ok(client.get(f"{BASE}/projects/{PROJECT}/datasets/{ds_id}/eda/report"), "eda/report")
    assert report["summary"]["num_rows"] == 4, report
    assert len(report["column_stats"]) == 3, report
    assert len(report["visualizations"]) > 0, report
    print(f"OK eda stats={len(report['column_stats'])} charts={len(report['visualizations'])}")

    create = client.post(
        f"{BASE}/projects/{PROJECT}/datasets",
        json={"name": "day2_img_smoke", "format": "image", "tags": ["smoke"]},
    )
    img_ds = ok(create, "create image dataset")
    img_id = img_ds["id"]
    detail = ok(client.get(f"{BASE}/projects/{PROJECT}/datasets/{img_id}"), "get image dataset")
    raw_dir = Path(detail["file_path"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        path = raw_dir / f"img_{i}.png"
        Image.new("RGB", (32, 32), color=(i * 80, 100, 150)).save(path)

    aug = client.post(
        f"{BASE}/projects/{PROJECT}/datasets/{img_id}/augment",
        json={
            "transforms": [{"type": "rotate", "params": {"angle": 10}}, {"type": "flip_horizontal", "params": {}}],
            "num_augmented": 1,
            "output_dataset_name": "day2_img_aug",
        },
    )
    aug_res = ok(aug, "augment")
    assert aug_res["original_count"] == 2, aug_res
    assert aug_res["augmented_count"] == 2, aug_res
    print(f"OK augment new_ds={aug_res['new_dataset_id']}")

    print("\nAll Day2 smoke checks passed.")


if __name__ == "__main__":
    main()
