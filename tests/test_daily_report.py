"""Tests for the daily discover-interpret-rank pipeline."""

from dataclasses import replace
from datetime import datetime

import pytest

from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.daily_report import run_daily_report
from kaggle_scout.user_profile import UserProfile


REFERENCE_TIME = datetime(2026, 11, 9, 6, 30)


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


class FakeSource:
    def __init__(self, competitions: list[Competition], fail_overview: str = "") -> None:
        self.competitions = competitions
        self.fail_overview = fail_overview
        self.reference_times: list[datetime] = []

    def discover_active(self, *, reference_time: datetime) -> list[Competition]:
        self.reference_times.append(reference_time)
        return self.competitions

    def load_overview(self, competition: Competition) -> Competition:
        if competition.title == self.fail_overview:
            raise RuntimeError("overview unavailable")
        return replace(competition, overview=f"Overview of {competition.title}")


class FakeInterpreter:
    def __init__(self, learning_values: dict[str, str], fail: str = "") -> None:
        self.learning_values = learning_values
        self.fail = fail
        self.seen_overviews: list[str | None] = []

    def analyze(self, competition: Competition) -> CompetitionInterpretation:
        self.seen_overviews.append(competition.overview)
        if competition.title == self.fail:
            raise TimeoutError("model timed out")
        return CompetitionInterpretation(
            problem_type="classification",
            domain="retail",
            skills_required=("python",),
            difficulty="intermediate",
            learning_value=self.learning_values[competition.title],
            reasoning="Example.",
        )


def test_run_daily_report_ranks_competitions_with_overviews() -> None:
    source = FakeSource([competition("Medium"), competition("High")])
    interpreter = FakeInterpreter({"Medium": "medium", "High": "high"})

    result = run_daily_report(
        profile=profile(),
        source=source,
        interpreter=interpreter,
        reference_time=REFERENCE_TIME,
    )

    assert source.reference_times == [REFERENCE_TIME]
    assert interpreter.seen_overviews == ["Overview of Medium", "Overview of High"]
    assert [item.competition.title for item in result.ranked] == ["High", "Medium"]
    assert result.failures == ()


def test_run_daily_report_records_failures_and_keeps_going() -> None:
    source = FakeSource(
        [competition("Ok"), competition("No overview"), competition("Slow")],
        fail_overview="No overview",
    )
    interpreter = FakeInterpreter({"Ok": "high", "Slow": "high"}, fail="Slow")

    result = run_daily_report(
        profile=profile(),
        source=source,
        interpreter=interpreter,
        reference_time=REFERENCE_TIME,
    )

    assert [item.competition.title for item in result.ranked] == ["Ok"]
    assert result.failures == (
        "No overview: RuntimeError: overview unavailable",
        "Slow: TimeoutError: model timed out",
    )


def test_run_daily_report_skips_excluded_competitions_entirely() -> None:
    source = FakeSource([competition("Seen"), competition("New")])
    interpreter = FakeInterpreter({"New": "high"})

    result = run_daily_report(
        profile=profile(),
        source=source,
        interpreter=interpreter,
        reference_time=REFERENCE_TIME,
        include=lambda item: item.title != "Seen",
    )

    assert interpreter.seen_overviews == ["Overview of New"]
    assert [item.competition.title for item in result.ranked] == ["New"]
    assert result.skipped == 1
    assert result.active_refs == ("Seen", "New")


def test_run_daily_report_propagates_discovery_failure() -> None:
    class BrokenSource(FakeSource):
        def discover_active(self, *, reference_time: datetime) -> list[Competition]:
            raise RuntimeError("Kaggle down")

    with pytest.raises(RuntimeError, match="Kaggle down"):
        run_daily_report(
            profile=profile(),
            source=BrokenSource([]),
            interpreter=FakeInterpreter({}),
            reference_time=REFERENCE_TIME,
        )
