"""Day3 smoke: split, EDA persist, encode extensions, image labels."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
from PIL import Image

BASE = "http://127.0.0.1:8000/api/v1"
DEFAULT_DEMO_PROJECT = "11111111-1111-1111-1111-111111111111"
CSV = "name,age,score,label\nAlice,30,88,A\nBob,25,92,B\nCharlie,35,70,A\nDiana,28,85,B\nEve,32,90,A\n"


def resolve_project_id(cli_value: str | None) -> str:
    if cli_value:
        return cli_value
    return os.environ.get("DEEPFLOW_SMOKE_PROJECT", DEFAULT_DEMO_PROJECT)


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
    parser = argparse.ArgumentParser(description="Day3 API smoke test")
    parser.add_argument(
        "--project-id",
        default=None,
        help="Project UUID (default: DEEPFLOW_SMOKE_PROJECT env or demo seed project)",
    )
    parser.add_argument("--base-url", default=BASE, help="API base URL")
    args = parser.parse_args()
    project = resolve_project_id(args.project_id)
    base = args.base_url.rstrip("/")

    client = httpx.Client(timeout=60.0)

    ok(client.get(f"{base}/health"), "health")
    print("OK health")

    files = {"file": ("day3_test.csv", CSV.encode("utf-8"), "text/csv")}
    form = {"name": "day3_test", "tags": "smoke,day3"}
    ds = ok(client.post(f"{base}/projects/{project}/datasets/upload", files=files, data=form), "upload")
    ds_id = ds["id"]
    assert ds["num_samples"] == 5, ds
    print(f"OK upload ds_id={ds_id}")

    eda_run = client.post(
        f"{base}/projects/{project}/datasets/{ds_id}/eda",
        json={"include_visualizations": False},
    )
    ok(eda_run, "eda")
    report = ok(client.get(f"{base}/projects/{project}/datasets/{ds_id}/eda/report"), "eda/report")
    assert report["summary"]["num_rows"] == 5, report
    print("OK eda + report")

    freq = ok(
        client.post(
            f"{base}/projects/{project}/datasets/{ds_id}/clean/encode",
            json={"columns": ["name"], "method": "frequency_encoding"},
        ),
        "encode/frequency",
    )
    assert freq["rows_after"] == 5, freq
    print("OK frequency_encoding")

    target = ok(
        client.post(
            f"{base}/projects/{project}/datasets/{ds_id}/clean/encode",
            json={"columns": ["label"], "method": "target_encoding", "target_column": "score"},
        ),
        "encode/target",
    )
    assert target["rows_after"] == 5, target
    print("OK target_encoding")

    split = ok(
        client.post(
            f"{base}/projects/{project}/datasets/{ds_id}/split",
            json={"ratios": {"train": 0.6, "val": 0.2, "test": 0.2}, "random_seed": 42},
        ),
        "split",
    )
    assert split["train_count"] + split["val_count"] + split["test_count"] == 5, split
    assert split["train_dataset_id"] != ds_id, split
    print(
        f"OK split train={split['train_count']} val={split['val_count']} test={split['test_count']}"
    )

    train_get = ok(
        client.get(f"{base}/projects/{project}/datasets/{split['train_dataset_id']}"),
        "get train split",
    )
    assert train_get["num_samples"] == split["train_count"], train_get
    print("OK train split dataset record")

    create = ok(
        client.post(
            f"{base}/projects/{project}/datasets",
            json={"name": "day3_img", "format": "image", "tags": ["smoke"]},
        ),
        "create image dataset",
    )
    img_ds_id = create["id"]
    detail = ok(client.get(f"{base}/projects/{project}/datasets/{img_ds_id}"), "get image dataset")
    raw_dir = Path(detail["file_path"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color=(100, 150, 200)).save(raw_dir / "sample_a.jpg")

    gallery = ok(
        client.get(
            f"{base}/projects/{project}/datasets/{img_ds_id}/images",
            params={"page": 1, "page_size": 10},
        ),
        "images",
    )
    assert gallery["total"] >= 1, gallery
    fname = gallery["items"][0]["filename"]
    print(f"OK images total={gallery['total']} first={fname}")

    labels = ok(
        client.put(
            f"{base}/projects/{project}/datasets/{img_ds_id}/labels",
            json={"items": [{"filename": fname, "labels": ["cat", "indoor"]}]},
        ),
        "labels",
    )
    assert labels["updated"] == 1, labels

    gallery2 = ok(
        client.get(
            f"{base}/projects/{project}/datasets/{img_ds_id}/images",
            params={"page": 1, "page_size": 10},
        ),
        "images after labels",
    )
    assert gallery2["items"][0]["labels"] == ["cat", "indoor"], gallery2
    print("OK labels persist")

    print("\nAll Day3 smoke checks passed.")


if __name__ == "__main__":
    main()
