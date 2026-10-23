"""Tests for ranking scored competitions."""

from datetime import datetime

from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.ranking import rank_competitions
from kaggle_scout.user_profile import UserProfile


def profile() -> UserProfile:
    return UserProfile(
        skills=("python",),
        experience_level="intermediate",
        interests=("classification",),
        preferred_difficulty_levels=("intermediate",),
        learning_goals=("practice",),
    )


def competition(title: str) -> Competition:
    return Competition(
        ref=title,
        title=title,
        deadline=datetime(2026, 12, 31),
        team_count=1,
    )


def interpretation(**overrides: object) -> CompetitionInterpretation:
    values = {
        "problem_type": "classification",
        "domain": "retail",
        "skills_required": ("python",),
        "difficulty": "intermediate",
        "learning_value": "high",
        "reasoning": "A classification task.",
    }
    values.update(overrides)
    return CompetitionInterpretation(**values)


def test_rank_competitions_sorts_by_score_then_title() -> None:
    ranked = rank_competitions(
        profile(),
        [
            (competition("Beta"), interpretation(learning_value="medium")),
            (competition("Alpha"), interpretation(learning_value="high")),
            (competition("Gamma"), interpretation(learning_value="high")),
        ],
    )

    assert [item.competition.title for item in ranked] == [
        "Alpha",
        "Gamma",
        "Beta",
    ]
    assert ranked[0].score.total_score > ranked[2].score.total_score
    assert ranked[0].explanation.summary.startswith("Recommended")
