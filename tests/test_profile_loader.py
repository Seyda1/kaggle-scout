"""Tests for loading a local user profile file."""

import json
from pathlib import Path

import pytest

from kaggle_scout.profile_loader import EXAMPLE_PROFILE_PATH, load_user_profile


def write_profile(path: Path, **overrides: object) -> Path:
    payload = {
        "skills": ["python"],
        "experience_level": "intermediate",
        "interests": ["classification"],
        "preferred_difficulty_levels": ["beginner"],
        "learning_goals": ["practice"],
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_user_profile_from_json_file(tmp_path: Path) -> None:
    path = write_profile(tmp_path / "user_profile.json")

    profile = load_user_profile(path)

    assert profile.skills == ("python",)
    assert profile.interests == ("classification",)
    assert profile.preferred_difficulty_levels == ("beginner",)


def test_example_profile_loads() -> None:
    profile = load_user_profile(EXAMPLE_PROFILE_PATH)

    assert profile.skills
    assert profile.experience_level == "intermediate"


def test_missing_profile_explains_how_to_create_it(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="user_profile.example.json"):
        load_user_profile(missing)


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "user_profile.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid JSON"):
        load_user_profile(path)


def test_profile_reuses_user_profile_validation(tmp_path: Path) -> None:
    path = write_profile(
        tmp_path / "user_profile.json",
        experience_level="expert",
    )

    with pytest.raises(ValueError, match="experience_level must be one of"):
        load_user_profile(path)
