"""Tests for deterministic recommendation scoring."""

import pytest

from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.recommendation import RecommendationEngine
from kaggle_scout.user_profile import UserProfile


def profile_with(**overrides: object) -> UserProfile:
    values = {
        "skills": ("python",),
        "experience_level": "intermediate",
        "interests": ("computer vision",),
        "preferred_difficulty_levels": ("intermediate",),
        "learning_goals": ("learn deep learning",),
    }
    values.update(overrides)
    return UserProfile(**values)


def interpretation_with(**overrides: object) -> CompetitionInterpretation:
    values = {
        "problem_type": "computer_vision",
        "domain": "image recognition",
        "skills_required": ("python",),
        "difficulty": "intermediate",
        "learning_value": "high",
        "reasoning": "A vision classification task.",
    }
    values.update(overrides)
    return CompetitionInterpretation(**values)


def score(
    profile: UserProfile | None = None,
    interpretation: CompetitionInterpretation | None = None,
):
    return RecommendationEngine().score(
        profile or profile_with(),
        interpretation or interpretation_with(),
    )


def test_normalization_applies_to_exact_skill_matching() -> None:
    result = score(
        profile_with(skills=("  Computer-Vision  ",)),
        interpretation_with(skills_required=("computer_vision",)),
    )

    assert result.skill_match == 1.0


def test_skill_match_is_fraction_of_unique_required_skills() -> None:
    result = score(
        profile_with(skills=("python", "pandas")),
        interpretation_with(skills_required=("python", "pandas", "xgboost")),
    )

    assert result.skill_match == pytest.approx(2 / 3)


def test_duplicate_skills_count_once() -> None:
    result = score(
        profile_with(skills=("python", "PYTHON")),
        interpretation_with(
            skills_required=("python", " Python ", "sql", "SQL")
        ),
    )

    assert result.skill_match == 0.5


@pytest.mark.parametrize(
    ("user_skills", "required_skills"),
    (
        ((), ("python",)),
        (("python",), ()),
        ((), ()),
    ),
)
def test_empty_skills_are_neutral(
    user_skills: tuple[str, ...],
    required_skills: tuple[str, ...],
) -> None:
    result = score(
        profile_with(skills=user_skills),
        interpretation_with(skills_required=required_skills),
    )

    assert result.skill_match == 0.5


def test_preferred_difficulty_matches() -> None:
    result = score(
        profile_with(preferred_difficulty_levels=("beginner", "advanced")),
        interpretation_with(difficulty="advanced"),
    )

    assert result.difficulty_match == 1.0


def test_unpreferred_difficulty_does_not_match() -> None:
    result = score(
        profile_with(preferred_difficulty_levels=("beginner",)),
        interpretation_with(difficulty="advanced"),
    )

    assert result.difficulty_match == 0.0


@pytest.mark.parametrize(
    ("preferences", "difficulty"),
    (
        ((), "beginner"),
        (("beginner",), "unknown"),
    ),
)
def test_unspecified_difficulty_information_is_neutral(
    preferences: tuple[str, ...],
    difficulty: str,
) -> None:
    result = score(
        profile_with(preferred_difficulty_levels=preferences),
        interpretation_with(difficulty=difficulty),
    )

    assert result.difficulty_match == 0.5


def test_interest_matches_normalized_problem_type() -> None:
    result = score(
        profile_with(interests=("Computer Vision",)),
        interpretation_with(domain="unrelated", problem_type="computer_vision"),
    )

    assert result.interest_match == 1.0


def test_interest_matches_whole_word_in_problem_type() -> None:
    result = score(
        profile_with(interests=("vision",)),
        interpretation_with(domain="unrelated", problem_type="computer_vision"),
    )

    assert result.interest_match == 1.0


def test_domain_does_not_count_toward_interest_match() -> None:
    result = score(
        profile_with(interests=("consumer behavior", "chemistry")),
        interpretation_with(
            domain="Chemistry and Consumer-Behavior",
            problem_type="classification",
        ),
    )

    assert result.interest_match == 0.0


def test_interest_does_not_match_inside_another_word() -> None:
    result = score(
        profile_with(interests=("regress",)),
        interpretation_with(problem_type="regression"),
    )

    assert result.interest_match == 0.0


@pytest.mark.parametrize(
    ("interests", "problem_type"),
    (
        ((), "classification"),
        (("classification",), "unknown"),
    ),
)
def test_unspecified_interest_information_is_neutral(
    interests: tuple[str, ...],
    problem_type: str,
) -> None:
    result = score(
        profile_with(interests=interests),
        interpretation_with(problem_type=problem_type),
    )

    assert result.interest_match == 0.5


@pytest.mark.parametrize(
    ("learning_value", "expected"),
    (
        ("low", 0.0),
        ("medium", 0.5),
        ("high", 1.0),
        ("unknown", 0.5),
    ),
)
def test_learning_value_mapping(learning_value: str, expected: float) -> None:
    result = score(interpretation=interpretation_with(learning_value=learning_value))

    assert result.learning_value == expected


def test_weighted_score_calculation() -> None:
    result = score(
        profile_with(
            skills=("python",),
            interests=("classification",),
            preferred_difficulty_levels=("advanced",),
        ),
        interpretation_with(
            skills_required=("python", "sql"),
            domain="healthcare",
            problem_type="classification",
            difficulty="advanced",
            learning_value="medium",
        ),
    )

    assert result.skill_match == 0.5
    assert result.difficulty_match == 1.0
    assert result.interest_match == 1.0
    assert result.learning_value == 0.5
    assert result.total_score == pytest.approx(0.65)


def test_score_remains_between_zero_and_one() -> None:
    lowest = score(
        profile_with(
            skills=("python",),
            interests=("vision",),
            preferred_difficulty_levels=("beginner",),
        ),
        interpretation_with(
            skills_required=("sql",),
            domain="finance",
            problem_type="regression",
            difficulty="advanced",
            learning_value="low",
        ),
    )
    highest = score()

    assert lowest.total_score == 0.0
    assert highest.total_score == 1.0
    assert 0.0 <= lowest.total_score <= 1.0
    assert 0.0 <= highest.total_score <= 1.0


def test_experience_and_learning_goals_do_not_affect_v1_score() -> None:
    first = score(
        profile_with(
            experience_level="beginner",
            learning_goals=("learn NLP",),
        )
    )
    second = score(
        profile_with(
            experience_level="advanced",
            learning_goals=("practice deployment",),
        )
    )

    assert first == second
