"""Ollama provider for structured competition interpretation."""

import json
from collections.abc import Sequence
from dataclasses import replace
from urllib.request import Request, urlopen

from kaggle_scout.analysis.interpretation import CompetitionInterpretation
from kaggle_scout.competition import Competition


class OllamaCompetitionProvider:
    """Interpret competitions using a locally running Ollama model."""

    # Same input, same answer: scores should only change when the data does.
    OPTIONS = {"temperature": 0, "seed": 42}

    def __init__(
        self,
        *,
        model: str = "qwen3:14b",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        learning_goals: Sequence[str] = (),
        skills: Sequence[str] = (),
        interests: Sequence[str] = (),
    ) -> None:
        self._model = model
        self._endpoint = f"{base_url.rstrip('/')}/api/generate"
        self._timeout = timeout
        self._learning_goals = tuple(
            goal.strip() for goal in learning_goals if goal.strip()
        )
        self._skills = tuple(skill.strip() for skill in skills if skill.strip())
        self._interests = tuple(
            interest.strip() for interest in interests if interest.strip()
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def instructions(self) -> str:
        """Instruction text sent before the competition, without user data."""
        parts = [self.INSTRUCTIONS]
        if self._learning_goals:
            parts.append(self.GOAL_INSTRUCTIONS)
        if self._skills:
            parts.append(self.SKILL_INSTRUCTIONS)
        if self._interests:
            parts.append(self.INTEREST_INSTRUCTIONS)
        return "".join(parts)

    def interpret(self, competition: Competition) -> CompetitionInterpretation:
        """Request and validate one structured competition interpretation."""
        payload = {
            "model": self._model,
            "prompt": self._build_prompt(competition),
            "stream": False,
            "format": "json",
            "think": False,
            "options": dict(self.OPTIONS),
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

        interpretation = CompetitionInterpretation(**interpretation_data)
        return replace(
            interpretation,
            matched_goals=self._known_goals(interpretation.matched_goals),
            skills_you_have=self._known_skills(interpretation.skills_you_have),
            skills_to_learn=self._skills_to_learn(interpretation.skills_to_learn),
            matched_interests=(
                self._known_interests(interpretation.matched_interests or ())
                if self._interests
                else None
            ),
        )

    def _known_goals(self, answered: tuple[str, ...]) -> tuple[str, ...]:
        # The model may reword a goal or invent one; keep only the user's own text.
        answered_keys = {goal.strip().casefold() for goal in answered}
        return tuple(
            goal for goal in self._learning_goals if goal.casefold() in answered_keys
        )

    def _known_interests(self, answered: tuple[str, ...]) -> tuple[str, ...]:
        answered_keys = {interest.strip().casefold() for interest in answered}
        return tuple(
            interest
            for interest in self._interests
            if interest.casefold() in answered_keys
        )

    def _known_skills(self, answered: tuple[str, ...]) -> tuple[str, ...]:
        answered_keys = {skill.strip().casefold() for skill in answered}
        return tuple(
            skill for skill in self._skills if skill.casefold() in answered_keys
        )

    def _skills_to_learn(self, answered: tuple[str, ...]) -> tuple[str, ...]:
        # Drop anything that is already on the profile, even under different casing.
        owned = {skill.casefold() for skill in self._skills}
        seen: set[str] = set()
        kept: list[str] = []
        for skill in answered:
            cleaned = skill.strip()
            key = cleaned.casefold()
            if not cleaned or key in owned or key in seen:
                continue
            seen.add(key)
            kept.append(cleaned)
        return tuple(kept)

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

    GOAL_INSTRUCTIONS = (
        "Also add the key matched_goals: an array of the user's learning "
        "goals listed below, copied exactly as written. Include a goal only "
        "when that goal is the main work of this competition. If you are "
        "unsure, leave it out.\n"
        "A goal about feature engineering matches only when the main task is "
        "building columns from a raw table. A goal about classification "
        "matches only when the main task is predicting a category from "
        "examples. A game, a bot, an agent, a puzzle, or an optimization "
        "task matches neither: use an empty array.\n"
        "Judge learning_value from the main work only: high if it directly "
        "practices a matched goal, medium if only partly, low if none. Name "
        "the matched goal in reasoning.\n"
    )

    SKILL_INSTRUCTIONS = (
        "Also add the keys skills_you_have and skills_to_learn.\n"
        "skills_you_have: user skills this competition actually requires, "
        "copied exactly. Do not copy the whole user skill list. pandas and "
        "scikit-learn count only for table data. feature engineering counts "
        "only when the task is building columns from raw data. machine "
        "learning counts only when the task is fitting a model on examples. "
        "For a game bot or agent, skills_you_have may contain only python, "
        "and skills_to_learn must name the missing agent skill.\n"
        "skills_to_learn: skills the competition needs that the user does "
        "not have. If the user has pandas, do not also list data analysis. "
        "Do not put a user skill into skills_to_learn.\n"
        "Keep skills_required as the full list of technical skills needed.\n"
    )

    INTEREST_INSTRUCTIONS = (
        "Also add the key matched_interests: an array of the user's "
        "interests listed below that this competition is about, copied "
        "exactly as written. If none fit, use an empty array. If you are "
        "unsure, leave the interest out.\n"
        "Tick an interest only when the subject of the competition is that "
        "interest. tabular data matches a table of rows and columns, "
        "including regression and time series. classification matches only "
        "when the main task is predicting a category. Do not tick an "
        "interest only because the problem type word is the same. A game, "
        "a photo contest, or a puzzle does not match tabular data, consumer "
        "behavior, or electric vehicles.\n"
    )

    def _build_prompt(self, competition: Competition) -> str:
        profile_lines = ""
        if self._learning_goals:
            profile_lines += (
                f"User learning goals: {json.dumps(list(self._learning_goals))}\n"
            )
        if self._skills:
            profile_lines += f"User skills: {json.dumps(list(self._skills))}\n"
        if self._interests:
            profile_lines += f"User interests: {json.dumps(list(self._interests))}\n"
        competition_data = {
            "title": competition.title,
            "description": competition.description,
            "overview": competition.overview,
            "tags": competition.tags,
            "deadline": competition.deadline.isoformat(),
            "category": competition.category,
            "reward": competition.reward,
            "evaluation_metric": competition.evaluation_metric,
        }
        return (
            f"{self.instructions}{profile_lines}"
            f"Competition: {json.dumps(competition_data)}"
        )
