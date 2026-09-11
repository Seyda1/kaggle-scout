"""Provider-independent boundary for LLM competition analysis."""

from typing import Protocol

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.competition import Competition


class CompetitionInterpretationProvider(Protocol):
    """Behavior required from a future LLM provider adapter."""

    def interpret(self, competition: Competition) -> CompetitionInterpretation:
        """Convert competition metadata into a structured interpretation."""
        ...


class LLMCompetitionAnalyzer:
    """Produce structured interpretations through an injected provider."""

    def __init__(self, provider: CompetitionInterpretationProvider) -> None:
        self._provider = provider

    def analyze(self, competition: Competition) -> CompetitionInterpretation:
        """Interpret one competition without exposing provider details."""
        interpretation = self._provider.interpret(competition)
        if not isinstance(interpretation, CompetitionInterpretation):
            raise TypeError(
                "interpretation provider must return CompetitionInterpretation"
            )
        return interpretation
