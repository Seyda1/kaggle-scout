"""Tests for threshold-based recommendation decisions."""

from dataclasses import FrozenInstanceError

import pytest

from kaggle_scout.recommendation import RecommendationScore
from kaggle_scout.recommendation_decision import (
    RecommendationDecider,
    RecommendationDecision,
)


def score_with_total(total_score: float) -> RecommendationScore:
    return RecommendationScore(
        skill_match=0.0,
        difficulty_match=0.0,
        interest_match=0.0,
        learning_value=0.0,
        total_score=total_score,
    )


@pytest.mark.parametrize(
    ("total_score", "expected_decision"),
    (
        (0.00, "not_recommended"),
        (0.499999, "not_recommended"),
        (0.50, "maybe"),
        (0.699999, "maybe"),
        (0.70, "recommended"),
        (1.00, "recommended"),
    ),
)
def test_decision_thresholds(
    total_score: float,
    expected_decision: str,
) -> None:
    score = score_with_total(total_score)

    result = RecommendationDecider().decide(score)

    assert result.score is score
    assert result.decision == expected_decision


def test_decision_result_is_immutable() -> None:
    result = RecommendationDecider().decide(score_with_total(0.70))

    with pytest.raises(FrozenInstanceError):
        setattr(result, "decision", "maybe")


def test_invalid_decision_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="decision must be one of"):
        RecommendationDecision(
            score=score_with_total(0.70),
            decision="strongly_recommended",
        )
