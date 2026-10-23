"""Deterministic explanations for recommendation decisions."""

from dataclasses import dataclass

from kaggle_scout.recommendation_decision import Decision, RecommendationDecision


@dataclass(frozen=True, slots=True)
class RecommendationExplanation:
    """Human-readable summary and structured signal reasons."""

    decision: Decision
    summary: str
    skill_reason: str
    difficulty_reason: str
    interest_reason: str
    learning_value_reason: str


class RecommendationExplainer:
    """Explain an existing decision without recalculating its score."""

    def explain(
        self,
        recommendation: RecommendationDecision,
    ) -> RecommendationExplanation:
        """Create a deterministic explanation from the existing breakdown."""
        score = recommendation.score
        label = {
            "recommended": "Recommended",
            "maybe": "Maybe",
            "not_recommended": "Not recommended",
        }[recommendation.decision]

        return RecommendationExplanation(
            decision=recommendation.decision,
            summary=f"{label} ({score.total_score:.0%})",
            skill_reason=self._skill_reason(score.skill_match),
            difficulty_reason=self._difficulty_reason(score.difficulty_match),
            interest_reason=self._interest_reason(score.interest_match),
            learning_value_reason=self._learning_value_reason(score.learning_value),
        )

    @staticmethod
    def _skill_reason(value: float) -> str:
        if value >= 0.8:
            return "Strong skill match"
        if value >= 0.5:
            return "Partial skill match"
        return "Limited skill match"

    @staticmethod
    def _difficulty_reason(value: float) -> str:
        if value == 1.0:
            return "Matches preferred difficulty"
        if value == 0.5:
            return "Difficulty preference is unspecified or unknown"
        return "Difficulty is outside the preferred range"

    @staticmethod
    def _interest_reason(value: float) -> str:
        if value == 1.0:
            return "Matches your interests"
        if value == 0.5:
            return "Interest alignment is unknown"
        return "Does not match your specified interests"

    @staticmethod
    def _learning_value_reason(value: float) -> str:
        if value == 1.0:
            return "High learning value"
        if value == 0.5:
            return "Medium or unknown learning value"
        return "Low learning value"
