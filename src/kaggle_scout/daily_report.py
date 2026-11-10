"""Discover, interpret, and rank active competitions for one profile."""

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


def run_daily_report(
    *,
    profile: UserProfile,
    source: ActiveCompetitionSource,
    interpreter: CompetitionInterpreter,
    reference_time: datetime,
) -> DailyReportResult:
    """Rank every active competition; one failed competition does not stop the run."""
    active = source.discover_active(reference_time=reference_time)

    interpreted: list[tuple[Competition, CompetitionInterpretation]] = []
    failures: list[str] = []
    for competition in active:
        try:
            detailed = source.load_overview(competition)
            interpreted.append((detailed, interpreter.analyze(detailed)))
        except Exception as error:
            failures.append(f"{competition.title}: {type(error).__name__}: {error}")

    return DailyReportResult(
        ranked=rank_competitions(profile, interpreted),
        failures=tuple(failures),
    )
