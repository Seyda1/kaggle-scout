"""Tests for the provider-independent LLM analyzer boundary."""

from datetime import datetime

import pytest

from kaggle_scout.analysis import CompetitionInterpretation, LLMCompetitionAnalyzer
from kaggle_scout.competition import Competition


class FakeInterpretationProvider:
    """In-memory provider test double with no network behavior."""

    def __init__(self, result: object) -> None:
        self.result = result
        self.received: list[Competition] = []

    def interpret(self, competition: Competition) -> object:
        self.received.append(competition)
        return self.result


def example_competition() -> Competition:
    return Competition(
        ref="example",
        title="Example Classification Competition",
        deadline=datetime(2026, 12, 31),
        team_count=42,
        description="Predict one category for each row.",
        tags=("classification", "tabular"),
        evaluation_metric="Log Loss",
    )


def example_interpretation() -> CompetitionInterpretation:
    return CompetitionInterpretation(
        problem_type="classification",
        domain="general",
        skills_required=("python", "machine learning"),
        difficulty="beginner",
        learning_value="high",
        reasoning="The target is categorical and the data is tabular.",
    )


def test_analyze_delegates_and_returns_structured_interpretation() -> None:
    competition = example_competition()
    expected = example_interpretation()
    provider = FakeInterpretationProvider(expected)

    actual = LLMCompetitionAnalyzer(provider).analyze(competition)

    assert actual is expected
    assert provider.received == [competition]


def test_constructing_analyzer_does_not_call_provider() -> None:
    provider = FakeInterpretationProvider(example_interpretation())

    LLMCompetitionAnalyzer(provider)

    assert provider.received == []


def test_rejects_non_interpretation_provider_result() -> None:
    provider = FakeInterpretationProvider({"problem_type": "classification"})

    with pytest.raises(
        TypeError,
        match="provider must return CompetitionInterpretation",
    ):
        LLMCompetitionAnalyzer(provider).analyze(example_competition())
