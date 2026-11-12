"""Discover, interpret, and rank active competitions for one profile."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.ranking import RankedRecommendation, rank_competitions
from kaggle_scout.user_profile import UserProfile


class ActiveCompetitionSource(Protocol):
    def discover_active(self, *, reference_time: datetime) -> list[Competition]: ...

    def load_overview(self, competition: Competition) -> Competition: ...


class CompetitionInterpreter(Protocol):
    def analyze(self, competition: Competition) -> CompetitionInterpretation: ...


@dataclass(frozen=True, slots=True)
class DailyReportResult:
    """Ranked competitions plus the ones that could not be analyzed."""

    ranked: list[RankedRecommendation]
    failures: tuple[str, ...]
    active_refs: tuple[str, ...] = ()
    skipped: int = 0


def run_daily_report(
    *,
    profile: UserProfile,
    source: ActiveCompetitionSource,
    interpreter: CompetitionInterpreter,
    reference_time: datetime,
    include: Callable[[Competition], bool] = lambda competition: True,
) -> DailyReportResult:
    """Rank active competitions that pass ``include``.

    Excluded competitions are not downloaded or analyzed. One failed
    competition does not stop the run.
    """
    active = source.discover_active(reference_time=reference_time)
    selected = [competition for competition in active if include(competition)]

    interpreted: list[tuple[Competition, CompetitionInterpretation]] = []
    failures: list[str] = []
    for competition in selected:
        try:
            detailed = source.load_overview(competition)
            interpreted.append((detailed, interpreter.analyze(detailed)))
        except Exception as error:
            failures.append(f"{competition.title}: {type(error).__name__}: {error}")

    return DailyReportResult(
        ranked=rank_competitions(profile, interpreted),
        failures=tuple(failures),
        active_refs=tuple(competition.ref for competition in active),
        skipped=len(active) - len(selected),
    )
