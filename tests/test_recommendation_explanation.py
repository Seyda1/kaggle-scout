"""Tests for deterministic recommendation explanations."""

from dataclasses import FrozenInstanceError

import pytest

from kaggle_scout.recommendation import RecommendationScore
from kaggle_scout.recommendation_decision import RecommendationDecider
from kaggle_scout.recommendation_explanation import RecommendationExplainer


def explain(
    *,
    skill_match: float = 0.5,
    difficulty_match: float = 0.5,
    interest_match: float = 0.5,
    learning_value: float = 0.5,
    total_score: float = 0.5,
):
    score = RecommendationScore(
        skill_match=skill_match,
        difficulty_match=difficulty_match,
        interest_match=interest_match,
        learning_value=learning_value,
        total_score=total_score,
    )
    decision = RecommendationDecider().decide(score)
    return RecommendationExplainer().explain(decision)


@pytest.mark.parametrize(
    ("total_score", "expected_decision", "expected_summary"),
    (
        (0.80, "recommended", "Recommended (80%)"),
        (0.60, "maybe", "Maybe (60%)"),
        (0.40, "not_recommended", "Not recommended (40%)"),
    ),
)
def test_decision_summaries(
    total_score: float,
    expected_decision: str,
    expected_summary: str,
) -> None:
    result = explain(total_score=total_score)

    assert result.decision == expected_decision
    assert result.summary == expected_summary


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (0.8, "Strong skill match"),
        (0.5, "Partial skill match"),
        (0.49, "Limited skill match"),
    ),
)
def test_skill_reasons(value: float, expected: str) -> None:
    assert explain(skill_match=value).skill_reason == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (1.0, "Matches preferred difficulty"),
        (0.5, "Difficulty preference is unspecified or unknown"),
        (0.0, "Difficulty is outside the preferred range"),
    ),
)
def test_difficulty_reasons(value: float, expected: str) -> None:
    assert explain(difficulty_match=value).difficulty_reason == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (1.0, "Matches your interests"),
        (0.5, "Interest alignment is unknown"),
        (0.0, "Does not match your specified interests"),
    ),
)
def test_interest_reasons(value: float, expected: str) -> None:
    assert explain(interest_match=value).interest_reason == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (1.0, "High learning value"),
        (0.5, "Medium or unknown learning value"),
        (0.0, "Low learning value"),
    ),
)
def test_learning_value_reasons(value: float, expected: str) -> None:
    assert explain(learning_value=value).learning_value_reason == expected


def test_total_score_is_formatted_as_percentage() -> None:
    assert explain(total_score=0.654).summary == "Maybe (65%)"


def test_explanation_is_immutable() -> None:
    result = explain()

    with pytest.raises(FrozenInstanceError):
        setattr(result, "summary", "Changed")
