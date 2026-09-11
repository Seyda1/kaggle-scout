"""Tests for the Ollama competition interpretation provider."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from kaggle_scout.analysis import (
    LLMCompetitionAnalyzer,
    OllamaCompetitionProvider,
)
from kaggle_scout.competition import Competition


class FakeHttpResponse:
    def __init__(self, body: dict[str, object]) -> None:
        self._body = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def example_competition() -> Competition:
    return Competition(
        ref="example",
        title="Example Vision Competition",
        deadline=datetime(2026, 12, 31),
        team_count=42,
        description="Classify objects in images.",
        tags=("image", "classification"),
        category="Featured",
        reward="10,000 USD",
        evaluation_metric="Log Loss",
    )


def ollama_body(**overrides: object) -> dict[str, object]:
    interpretation = {
        "problem_type": "computer_vision",
        "domain": "image recognition",
        "skills_required": ["python", "deep learning"],
        "difficulty": "intermediate",
        "learning_value": "high",
        "reasoning": "The task classifies objects from image data.",
    }
    interpretation.update(overrides)
    return {"response": json.dumps(interpretation)}


def test_provider_returns_valid_interpretation_and_sends_expected_request() -> None:
    provider = OllamaCompetitionProvider(timeout=15)

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(ollama_body()),
    ) as mocked_urlopen:
        result = LLMCompetitionAnalyzer(provider).analyze(example_competition())

    assert result.problem_type == "computer_vision"
    assert result.skills_required == ("python", "deep learning")
    assert result.difficulty == "intermediate"
    assert result.learning_value == "high"

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://localhost:11434/api/generate"
    assert request.method == "POST"
    assert mocked_urlopen.call_args.kwargs["timeout"] == 15
    assert payload["model"] == "qwen3:14b"
    assert payload["stream"] is False
    assert payload["format"] == "json"
    assert payload["think"] is False
    assert "Example Vision Competition" in payload["prompt"]
    assert "exactly these keys" in payload["prompt"]


def test_provider_reuses_interpretation_validation() -> None:
    provider = OllamaCompetitionProvider()

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(ollama_body(difficulty="expert")),
    ):
        with pytest.raises(ValueError, match="difficulty must be one of"):
            provider.interpret(example_competition())


def test_provider_rejects_extra_json_fields() -> None:
    provider = OllamaCompetitionProvider()

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(ollama_body(unexpected="value")),
    ):
        with pytest.raises(TypeError, match="unexpected"):
            provider.interpret(example_competition())


def test_provider_rejects_malformed_model_json() -> None:
    provider = OllamaCompetitionProvider()

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse({"response": "not JSON"}),
    ):
        with pytest.raises(json.JSONDecodeError):
            provider.interpret(example_competition())
