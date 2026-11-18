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


def test_matched_goals_default_to_empty_and_become_a_tuple() -> None:
    assert interpretation_with().matched_goals == ()
    assert interpretation_with(matched_goals=["practice"]).matched_goals == (
        "practice",
    )


def test_matched_interests_default_to_unset_and_become_a_tuple() -> None:
    assert interpretation_with().matched_interests is None
    assert interpretation_with(matched_interests=["tabular data"]).matched_interests == (
        "tabular data",
    )
    assert interpretation_with(matched_interests=[]).matched_interests == ()


def test_skill_breakdown_fields_default_to_empty_and_become_tuples() -> None:
    assert interpretation_with().skills_you_have == ()
    assert interpretation_with().skills_to_learn == ()
    assert interpretation_with(skills_you_have=["python"]).skills_you_have == (
        "python",
    )
    assert interpretation_with(skills_to_learn=["sql"]).skills_to_learn == ("sql",)


@pytest.mark.parametrize("matched_goals", ("practice", ("practice", 1)))
def test_matched_goals_must_be_strings_in_a_collection(matched_goals: object) -> None:
    with pytest.raises(TypeError, match="matched_goals"):
        interpretation_with(matched_goals=matched_goals)


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
