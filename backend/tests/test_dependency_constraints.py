from pathlib import Path


def test_bcrypt_is_pinned_below_passlib_incompatible_major_version() -> None:
    requirements = Path(__file__).resolve().parents[2] / "requirements.txt"
    content = requirements.read_text(encoding="utf-8")

    assert "bcrypt>=4.0.0,<4.1.0" in content
