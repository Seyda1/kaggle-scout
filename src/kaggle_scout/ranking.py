"""Rank interpreted competitions by recommendation score."""

from dataclasses import dataclass

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.recommendation import RecommendationEngine, RecommendationScore
from kaggle_scout.recommendation_decision import (
    RecommendationDecider,
    RecommendationDecision,
)
from kaggle_scout.recommendation_explanation import (
    RecommendationExplainer,
    RecommendationExplanation,
)
from kaggle_scout.user_profile import UserProfile


@dataclass(frozen=True, slots=True)
class RankedRecommendation:
    """One scored competition and its explanation."""

    competition: Competition
    interpretation: CompetitionInterpretation
    decision: RecommendationDecision
    explanation: RecommendationExplanation

    @property
    def score(self) -> RecommendationScore:
        return self.decision.score


def rank_competitions(
    profile: UserProfile,
    interpreted: list[tuple[Competition, CompetitionInterpretation]],
) -> list[RankedRecommendation]:
    """Score each interpretation and return the highest totals first."""
    engine = RecommendationEngine()
    decider = RecommendationDecider()
    explainer = RecommendationExplainer()

    ranked: list[RankedRecommendation] = []
    for competition, interpretation in interpreted:
        decision = decider.decide(engine.score(profile, interpretation))
        ranked.append(
            RankedRecommendation(
                competition=competition,
                interpretation=interpretation,
                decision=decision,
                explanation=explainer.explain(decision),
            )
        )

    ranked.sort(
        key=lambda item: (
            -item.score.total_score,
            item.competition.title.casefold(),
        )
    )
    return ranked
