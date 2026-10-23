"""Deterministic decision layer for recommendation scores."""

from dataclasses import dataclass
from typing import Literal, get_args

from kaggle_scout.recommendation import RecommendationScore


Decision = Literal["recommended", "maybe", "not_recommended"]
_ALLOWED_DECISIONS = frozenset(get_args(Decision))


@dataclass(frozen=True, slots=True)
class RecommendationDecision:
    """A score breakdown paired with its threshold-based decision."""

    score: RecommendationScore
    decision: Decision

    def __post_init__(self) -> None:
        if not isinstance(self.score, RecommendationScore):
            raise TypeError("score must be a RecommendationScore")
        if self.decision not in _ALLOWED_DECISIONS:
            allowed = ", ".join(sorted(_ALLOWED_DECISIONS))
            raise ValueError(f"decision must be one of: {allowed}")


class RecommendationDecider:
    """Map a recommendation score to one of three decision states."""

    RECOMMENDED_THRESHOLD = 0.70
    MAYBE_THRESHOLD = 0.50

    def decide(self, score: RecommendationScore) -> RecommendationDecision:
        """Apply v1 thresholds without changing the score."""
        if score.total_score >= self.RECOMMENDED_THRESHOLD:
            decision: Decision = "recommended"
        elif score.total_score >= self.MAYBE_THRESHOLD:
            decision = "maybe"
        else:
            decision = "not_recommended"

        return RecommendationDecision(score=score, decision=decision)
