"""Ollama provider for structured competition interpretation."""

import json
from urllib.request import Request, urlopen

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.competition import Competition


class OllamaCompetitionProvider:
    """Interpret competitions using a locally running Ollama model."""

    def __init__(
        self,
        *,
        model: str = "qwen3:14b",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ) -> None:
        self._model = model
        self._endpoint = f"{base_url.rstrip('/')}/api/generate"
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    def interpret(self, competition: Competition) -> CompetitionInterpretation:
        """Request and validate one structured competition interpretation."""
        payload = {
            "model": self._model,
            "prompt": self._build_prompt(competition),
            "stream": False,
            "format": "json",
            "think": False,
        }
        request = Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=self._timeout) as response:
            ollama_response = json.loads(response.read().decode("utf-8"))

        interpretation_data = json.loads(ollama_response["response"])
        if not isinstance(interpretation_data, dict):
            raise TypeError("Ollama interpretation must be a JSON object")

        return CompetitionInterpretation(**interpretation_data)

    INSTRUCTIONS = (
        "Analyze this Kaggle competition. Return only one JSON object with "
        "exactly these keys: problem_type, domain, skills_required, "
        "difficulty, learning_value, reasoning.\n"
        "problem_type must be one of: classification, regression, "
        "time_series, nlp, computer_vision, recommendation, clustering, "
        "reinforcement_learning, other, unknown.\n"
        "difficulty must be one of: beginner, intermediate, advanced, "
        "unknown.\n"
        "learning_value must be one of: low, medium, high, unknown.\n"
        "domain and reasoning must be strings. skills_required must be an "
        "array of strings. Keep reasoning short.\n"
        "skills_required must contain only technical skills needed to "
        "participate, such as python, machine learning, data analysis, "
        "deep learning, or feature engineering. Do not include industry, "
        "sector, or subject-matter knowledge (for example healthcare, "
        "automotive, biology, or chemistry knowledge). Describe the "
        "sector only in domain.\n"
    )

    @classmethod
    def _build_prompt(cls, competition: Competition) -> str:
        competition_data = {
            "title": competition.title,
            "description": competition.description,
            "overview": competition.overview,
            "tags": competition.tags,
            "deadline": competition.deadline.isoformat(),
            "category": competition.category,
            "reward": competition.reward,
            "evaluation_metric": competition.evaluation_metric,
            "team_count": competition.team_count,
        }
        return f"{cls.INSTRUCTIONS}Competition: {json.dumps(competition_data)}"
