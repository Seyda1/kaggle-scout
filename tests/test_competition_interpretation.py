"""Tests for the provider-independent interpretation contract."""

from dataclasses import FrozenInstanceError

import pytest

from kaggle_scout.analysis import CompetitionInterpretation


PROBLEM_TYPES = (
    "classification",
    "regression",
    "time_series",
    "nlp",
    "computer_vision",
    "recommendation",
    "clustering",
    "reinforcement_learning",
    "other",
    "unknown",
)
DIFFICULTIES = ("beginner", "intermediate", "advanced", "unknown")
LEARNING_VALUES = ("low", "medium", "high", "unknown")


def interpretation_with(**overrides: object) -> CompetitionInterpretation:
    values = {
        "problem_type": "classification",
        "domain": "healthcare",
        "skills_required": ("python", "machine learning"),
        "difficulty": "intermediate",
        "learning_value": "high",
        "reasoning": "The task predicts one category from tabular inputs.",
    }
    values.update(overrides)
    return CompetitionInterpretation(**values)


def test_valid_construction() -> None:
    interpretation = interpretation_with()

    assert interpretation.problem_type == "classification"
    assert interpretation.domain == "healthcare"
    assert interpretation.skills_required == ("python", "machine learning")
    assert interpretation.difficulty == "intermediate"
    assert interpretation.learning_value == "high"
    assert interpretation.reasoning.startswith("The task predicts")


@pytest.mark.parametrize("problem_type", PROBLEM_TYPES)
def test_all_problem_types_are_allowed(problem_type: str) -> None:
    assert interpretation_with(problem_type=problem_type).problem_type == problem_type


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_all_difficulties_are_allowed(difficulty: str) -> None:
    assert interpretation_with(difficulty=difficulty).difficulty == difficulty


@pytest.mark.parametrize("learning_value", LEARNING_VALUES)
def test_all_learning_values_are_allowed(learning_value: str) -> None:
    assert (
        interpretation_with(learning_value=learning_value).learning_value
        == learning_value
    )


def test_invalid_problem_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="problem_type must be one of"):
        interpretation_with(problem_type="forecasting")


def test_invalid_difficulty_is_rejected() -> None:
    with pytest.raises(ValueError, match="difficulty must be one of"):
        interpretation_with(difficulty="expert")


def test_invalid_learning_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="learning_value must be one of"):
        interpretation_with(learning_value="very_high")


def test_skills_required_is_immutable() -> None:
    source_skills = ["python", "pandas"]

    interpretation = interpretation_with(skills_required=source_skills)
    source_skills.append("sql")

    assert interpretation.skills_required == ("python", "pandas")
    assert isinstance(interpretation.skills_required, tuple)
    with pytest.raises(FrozenInstanceError):
        setattr(interpretation, "skills_required", ("python",))


@pytest.mark.parametrize(
    "missing_field",
    (
        "problem_type",
        "domain",
        "skills_required",
        "difficulty",
        "learning_value",
        "reasoning",
    ),
)
def test_all_fields_are_required(missing_field: str) -> None:
    values = {
        "problem_type": "classification",
        "domain": "healthcare",
        "skills_required": ("python",),
        "difficulty": "beginner",
        "learning_value": "medium",
        "reasoning": "A short explanation.",
    }
    del values[missing_field]

    with pytest.raises(TypeError):
        CompetitionInterpretation(**values)
