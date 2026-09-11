"""Pure, deterministic facts derived from competition metadata."""

from dataclasses import dataclass
from datetime import datetime
from math import floor

from kaggle_scout.competition import Competition


@dataclass(frozen=True, slots=True)
class CompetitionAnalysis:
    """Objectively computed facts for one competition."""

    competition: Competition
    days_until_deadline: int
    has_deadline: bool
    has_evaluation_metric: bool
    normalized_tags: tuple[str, ...]


class CompetitionAnalyzer:
    """Compute deterministic facts without external dependencies."""

    def analyze(
        self,
        competition: Competition,
        *,
        reference_time: datetime,
    ) -> CompetitionAnalysis:
        """Analyze a competition relative to an explicit reference time."""
        seconds_until_deadline = (
            competition.deadline - reference_time
        ).total_seconds()

        return CompetitionAnalysis(
            competition=competition,
            days_until_deadline=floor(seconds_until_deadline / 86_400),
            has_deadline=competition.deadline is not None,
            has_evaluation_metric=self._has_meaningful_text(
                competition.evaluation_metric
            ),
            normalized_tags=self._normalize_tags(competition.tags),
        )

    @staticmethod
    def _has_meaningful_text(value: str | None) -> bool:
        return bool(value and value.strip())

    @staticmethod
    def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()

        for tag in tags or ():
            value = tag.strip().casefold()
            if value and value not in seen:
                normalized.append(value)
                seen.add(value)

        return tuple(normalized)
