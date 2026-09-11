"""Tests for deterministic competition analysis."""

from datetime import datetime

import pytest

from kaggle_scout.analysis import CompetitionAnalyzer
from kaggle_scout.competition import Competition


def competition_with(
    *,
    deadline: datetime = datetime(2026, 1, 4, 6),
    evaluation_metric: str | None = None,
    tags: tuple[str, ...] = (),
) -> Competition:
    return Competition(
        ref="example",
        title="Example Competition",
        deadline=deadline,
        team_count=10,
        evaluation_metric=evaluation_metric,
        tags=tags,
    )


def test_calculates_complete_days_until_deadline() -> None:
    competition = competition_with()
    analysis = CompetitionAnalyzer().analyze(
        competition,
        reference_time=datetime(2026, 1, 1, 12),
    )

    assert analysis.competition is competition
    assert analysis.days_until_deadline == 2
    assert analysis.has_deadline is True


def test_expired_partial_day_rounds_down_to_negative_one() -> None:
    analysis = CompetitionAnalyzer().analyze(
        competition_with(deadline=datetime(2026, 1, 1, 6)),
        reference_time=datetime(2026, 1, 1, 12),
    )

    assert analysis.days_until_deadline == -1


def test_evaluation_metric_is_present() -> None:
    analysis = CompetitionAnalyzer().analyze(
        competition_with(evaluation_metric="Log Loss"),
        reference_time=datetime(2026, 1, 1),
    )

    assert analysis.has_evaluation_metric is True


@pytest.mark.parametrize("evaluation_metric", [None, "", "   "])
def test_missing_evaluation_metric(evaluation_metric: str | None) -> None:
    analysis = CompetitionAnalyzer().analyze(
        competition_with(evaluation_metric=evaluation_metric),
        reference_time=datetime(2026, 1, 1),
    )

    assert analysis.has_evaluation_metric is False


def test_normalizes_tags_in_stable_order() -> None:
    analysis = CompetitionAnalyzer().analyze(
        competition_with(
            tags=("Computer Vision", " computer vision ", "NLP", "", "  ")
        ),
        reference_time=datetime(2026, 1, 1),
    )

    assert analysis.normalized_tags == ("computer vision", "nlp")


def test_empty_tags_remain_empty() -> None:
    analysis = CompetitionAnalyzer().analyze(
        competition_with(tags=()),
        reference_time=datetime(2026, 1, 1),
    )

    assert analysis.normalized_tags == ()


def test_result_depends_on_explicit_reference_time() -> None:
    analyzer = CompetitionAnalyzer()
    competition = competition_with(deadline=datetime(2026, 1, 10))

    earlier = analyzer.analyze(
        competition,
        reference_time=datetime(2026, 1, 1),
    )
    later = analyzer.analyze(
        competition,
        reference_time=datetime(2026, 1, 5),
    )

    assert earlier.days_until_deadline == 9
    assert later.days_until_deadline == 5
