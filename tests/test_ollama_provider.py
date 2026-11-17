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
        overview="## Description\n\nClassify objects in images from labeled photos.",
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
    assert payload["options"] == {"temperature": 0, "seed": 42}
    assert "Example Vision Competition" in payload["prompt"]
    assert "Classify objects in images from labeled photos." in payload["prompt"]
    assert "exactly these keys" in payload["prompt"]
    assert "skills_required must contain only technical skills" in payload["prompt"]
    assert "Describe the sector only in domain" in payload["prompt"]
    assert "team_count" not in payload["prompt"]


def test_without_learning_goals_the_prompt_has_no_goal_rules() -> None:
    provider = OllamaCompetitionProvider()

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(ollama_body()),
    ) as mocked_urlopen:
        result = provider.interpret(example_competition())

    prompt = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))["prompt"]
    assert "matched_goals" not in prompt
    assert "User learning goals" not in prompt
    assert provider.instructions == OllamaCompetitionProvider.INSTRUCTIONS
    assert result.matched_goals == ()


def test_learning_goals_are_sent_and_matched_goals_returned() -> None:
    provider = OllamaCompetitionProvider(
        learning_goals=("practice feature engineering", "learn computer vision")
    )

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(
            ollama_body(matched_goals=["learn computer vision"])
        ),
    ) as mocked_urlopen:
        result = provider.interpret(example_competition())

    prompt = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))["prompt"]
    assert (
        'User learning goals: ["practice feature engineering", "learn computer vision"]'
        in prompt
    )
    assert "only when that goal is the main work" in prompt
    assert provider.instructions.endswith(OllamaCompetitionProvider.GOAL_INSTRUCTIONS)
    assert result.matched_goals == ("learn computer vision",)


def test_matched_goals_keep_only_the_users_own_goals() -> None:
    provider = OllamaCompetitionProvider(
        learning_goals=("Practice feature engineering", "learn computer vision")
    )

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(
            ollama_body(
                matched_goals=[
                    "learn computer vision",
                    "practice feature engineering ",
                    "win a medal",
                ]
            )
        ),
    ):
        result = provider.interpret(example_competition())

    assert result.matched_goals == (
        "Practice feature engineering",
        "learn computer vision",
    )


def test_user_skills_are_sent_and_skill_breakdown_returned() -> None:
    provider = OllamaCompetitionProvider(
        skills=("python", "pandas", "scikit-learn")
    )

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(
            ollama_body(
                skills_you_have=["python", "pandas"],
                skills_to_learn=["deep learning"],
            )
        ),
    ) as mocked_urlopen:
        result = provider.interpret(example_competition())

    prompt = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))["prompt"]
    assert 'User skills: ["python", "pandas", "scikit-learn"]' in prompt
    assert "this competition actually requires" in prompt
    assert provider.instructions.endswith(OllamaCompetitionProvider.SKILL_INSTRUCTIONS)
    assert result.skills_you_have == ("python", "pandas")
    assert result.skills_to_learn == ("deep learning",)


def test_skill_breakdown_keeps_only_known_have_and_drops_owned_from_learn() -> None:
    provider = OllamaCompetitionProvider(skills=("Python", "pandas"))

    with patch(
        "kaggle_scout.analysis.ollama_provider.urlopen",
        return_value=FakeHttpResponse(
            ollama_body(
                skills_you_have=["python", "made up skill"],
                skills_to_learn=["pandas", "deep learning", " Deep Learning "],
            )
        ),
    ):
        result = provider.interpret(example_competition())

    assert result.skills_you_have == ("Python",)
    assert result.skills_to_learn == ("deep learning",)


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
