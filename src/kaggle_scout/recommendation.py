"""Deterministic and explainable competition scoring."""

from dataclasses import dataclass

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.user_profile import UserProfile


@dataclass(frozen=True, slots=True)
class RecommendationScore:
    """Normalized recommendation signals and their weighted total."""

    skill_match: float
    difficulty_match: float
    interest_match: float
    learning_value: float
    total_score: float


class RecommendationEngine:
    """Score competition fit using fixed deterministic rules."""

    SKILL_WEIGHT = 0.30
    DIFFICULTY_WEIGHT = 0.10
    INTEREST_WEIGHT = 0.20
    LEARNING_VALUE_WEIGHT = 0.40

    def score(
        self,
        profile: UserProfile,
        interpretation: CompetitionInterpretation,
    ) -> RecommendationScore:
        """Return the signal breakdown and weighted score."""
        skill_match = self._score_skills(profile.skills, interpretation)
        difficulty_match = self._score_difficulty(
            profile.preferred_difficulty_levels,
            interpretation.difficulty,
        )
        interest_match = self._score_interests(
            profile.interests,
            interpretation.problem_type,
        )
        learning_value = self._score_learning_value(
            interpretation.learning_value
        )

        total_score = (
            self.SKILL_WEIGHT * skill_match
            + self.DIFFICULTY_WEIGHT * difficulty_match
            + self.INTEREST_WEIGHT * interest_match
            + self.LEARNING_VALUE_WEIGHT * learning_value
        )

        return RecommendationScore(
            skill_match=skill_match,
            difficulty_match=difficulty_match,
            interest_match=interest_match,
            learning_value=learning_value,
            total_score=min(1.0, max(0.0, total_score)),
        )

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.strip().casefold().replace("_", " ").replace("-", " ")
        return " ".join(value.split())

    @classmethod
    def _score_skills(
        cls,
        user_skills: tuple[str, ...],
        interpretation: CompetitionInterpretation,
    ) -> float:
        # Prefer Qwen's have/learn lists when present (Option C, step 5).
        have = interpretation.skills_you_have
        learn = interpretation.skills_to_learn
        if have or learn:
            return len(have) / (len(have) + len(learn))
        return cls._score_skills_exact(user_skills, interpretation.skills_required)

    @classmethod
    def _score_skills_exact(
        cls,
        user_skills: tuple[str, ...],
        required_skills: tuple[str, ...],
    ) -> float:
        normalized_user = {cls._normalize(skill) for skill in user_skills}
        normalized_required = {
            cls._normalize(skill) for skill in required_skills
        }
        normalized_user.discard("")
        normalized_required.discard("")

        if not normalized_user or not normalized_required:
            return 0.5
        return len(normalized_user & normalized_required) / len(normalized_required)

    @staticmethod
    def _score_difficulty(
        preferred_difficulties: tuple[str, ...],
        competition_difficulty: str,
    ) -> float:
        if competition_difficulty == "unknown" or not preferred_difficulties:
            return 0.5
        return 1.0 if competition_difficulty in preferred_difficulties else 0.0

    @classmethod
    def _score_interests(
        cls,
        user_interests: tuple[str, ...],
        problem_type: str,
    ) -> float:
        # Domain is context only and intentionally excluded from matching.
        interests = {cls._normalize(interest) for interest in user_interests}
        interests.discard("")
        if not interests:
            return 0.5

        candidate = cls._normalize(problem_type)
        if candidate in {"", "unknown"}:
            return 0.5

        return (
            1.0
            if any(cls._phrases_match(interest, candidate) for interest in interests)
            else 0.0
        )

    @staticmethod
    def _phrases_match(first: str, second: str) -> bool:
        if first == second:
            return True
        padded_first = f" {first} "
        padded_second = f" {second} "
        return padded_first in padded_second or padded_second in padded_first

    @staticmethod
    def _score_learning_value(learning_value: str) -> float:
        return {
            "low": 0.0,
            "medium": 0.5,
            "high": 1.0,
            "unknown": 0.5,
        }[learning_value]
