"""Idempotent dev seed — matches demo project UUID used by frontend MSW."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infra.db.models import Dataset, DatasetFormat, DatasetStatus
from src.infra.db.models.project import Project
from src.infra.db.models.user import User, UserRole

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_PROJECT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

DEMO_USER = {
    "username": "demo",
    "password": "demo123",
}


def seed_demo_user(db: Session) -> None:
    if db.get(User, DEMO_USER_ID):
        return
    from app.core.security import hash_password
    db.add(User(
        id=DEMO_USER_ID,
        username=DEMO_USER["username"],
        password_hash=hash_password(DEMO_USER["password"]),
        role=UserRole.DEVELOPER,
    ))
    db.commit()


def seed_demo_project(db: Session) -> None:
    if db.get(Project, DEMO_PROJECT_ID):
        return
    db.add(Project(
        id=DEMO_PROJECT_ID,
        name="Demo Project",
        description="Auto-seeded demo project",
        owner_id=DEMO_USER_ID,
    ))
    db.commit()


def seed_demo_datasets(db: Session) -> None:
    exists = db.scalar(select(Dataset.id).where(Dataset.project_id == DEMO_PROJECT_ID).limit(1))
    if exists:
        return
    samples = [
        {
            "name": "iris_sample",
            "format": DatasetFormat.CSV,
            "file_path": f"projects/{DEMO_PROJECT_ID}/datasets/iris/raw/iris.csv",
            "num_samples": 150,
            "columns_meta": [
                {"name": "sepal_length", "dtype": "float64", "nullable": False},
                {"name": "species", "dtype": "object", "nullable": False},
            ],
            "tags": ["demo", "tabular"],
            "status": DatasetStatus.READY,
        },
        {
            "name": "cats_dogs",
            "format": DatasetFormat.IMAGE,
            "file_path": f"projects/{DEMO_PROJECT_ID}/datasets/cats/raw/",
            "num_samples": 200,
            "columns_meta": [{"name": "label", "dtype": "object", "nullable": True}],
            "tags": ["cv"],
            "status": DatasetStatus.READY,
        },
    ]
    for item in samples:
        db.add(Dataset(project_id=DEMO_PROJECT_ID, **item))
    db.commit()
