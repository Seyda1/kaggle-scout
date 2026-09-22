"""Tests for the application-level user profile."""

from dataclasses import FrozenInstanceError

import pytest

from kaggle_scout.user_profile import UserProfile


def profile_with(**overrides: object) -> UserProfile:
    values = {
        "skills": ("python", "machine learning"),
        "experience_level": "intermediate",
        "interests": ("computer vision", "tabular data"),
        "preferred_difficulty_levels": ("beginner", "intermediate"),
        "learning_goals": ("learn deep learning", "practice feature engineering"),
    }
    values.update(overrides)
    return UserProfile(**values)


def test_valid_profile() -> None:
    profile = profile_with()

    assert profile.skills == ("python", "machine learning")
    assert profile.experience_level == "intermediate"
    assert profile.interests == ("computer vision", "tabular data")
    assert profile.preferred_difficulty_levels == ("beginner", "intermediate")
    assert profile.learning_goals == (
        "learn deep learning",
        "practice feature engineering",
    )


@pytest.mark.parametrize(
    "experience_level",
    ("beginner", "intermediate", "advanced", "unknown"),
)
def test_allowed_experience_levels(experience_level: str) -> None:
    assert profile_with(experience_level=experience_level).experience_level == (
        experience_level
    )


@pytest.mark.parametrize(
    "difficulty",
    ("beginner", "intermediate", "advanced"),
)
def test_allowed_preferred_difficulties(difficulty: str) -> None:
    profile = profile_with(preferred_difficulty_levels=(difficulty,))

    assert profile.preferred_difficulty_levels == (difficulty,)


def test_invalid_experience_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="experience_level must be one of"):
        profile_with(experience_level="expert")


def test_invalid_preferred_difficulty_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="preferred_difficulty_levels must be one of",
    ):
        profile_with(preferred_difficulty_levels=("unknown",))


def test_collections_are_immutable_copies() -> None:
    source_skills = ["python"]

    profile = profile_with(skills=source_skills)
    source_skills.append("sql")

    assert profile.skills == ("python",)
    assert isinstance(profile.skills, tuple)
    with pytest.raises(FrozenInstanceError):
        setattr(profile, "skills", ("sql",))


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("skills", ("python", 1)),
        ("interests", ("vision", None)),
        ("learning_goals", (object(),)),
    ),
)
def test_non_string_collection_items_are_rejected(
    field_name: str,
    value: tuple[object, ...],
) -> None:
    with pytest.raises(TypeError, match="must contain only strings"):
        profile_with(**{field_name: value})


@pytest.mark.parametrize(
    "field_name",
    ("skills", "interests", "learning_goals"),
)
def test_blank_collection_items_are_rejected(field_name: str) -> None:
    with pytest.raises(ValueError, match="must not contain blank strings"):
        profile_with(**{field_name: ("   ",)})


def test_empty_collections_are_allowed() -> None:
    profile = profile_with(
        skills=(),
        interests=(),
        preferred_difficulty_levels=(),
        learning_goals=(),
    )

    assert profile.skills == ()
    assert profile.interests == ()
    assert profile.preferred_difficulty_levels == ()
    assert profile.learning_goals == ()


@pytest.mark.parametrize(
    "missing_field",
    (
        "skills",
        "experience_level",
        "interests",
        "preferred_difficulty_levels",
        "learning_goals",
    ),
)
def test_all_fields_are_required(missing_field: str) -> None:
    values = {
        "skills": ("python",),
        "experience_level": "beginner",
        "interests": ("tabular data",),
        "preferred_difficulty_levels": ("beginner",),
        "learning_goals": ("practice modeling",),
    }
    del values[missing_field]

    with pytest.raises(TypeError):
        UserProfile(**values)
