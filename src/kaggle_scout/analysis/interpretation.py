"""Provider-independent contract for LLM competition interpretation."""

from dataclasses import dataclass
from typing import Literal, get_args


ProblemType = Literal[
    "classification",
    "regression",
    "time_series",
    "nlp",
    "computer_vision",
    "recommendation",
    "clustering",
    "reinforcement_learning",
    "other",
    "unknown",
]
Difficulty = Literal["beginner", "intermediate", "advanced", "unknown"]
LearningValue = Literal["low", "medium", "high", "unknown"]

_ALLOWED_PROBLEM_TYPES = frozenset(get_args(ProblemType))
_ALLOWED_DIFFICULTIES = frozenset(get_args(Difficulty))
_ALLOWED_LEARNING_VALUES = frozenset(get_args(LearningValue))


@dataclass(frozen=True, slots=True)
class CompetitionInterpretation:
    """Structured interpretation produced by a future LLM analyzer."""

    problem_type: ProblemType
    domain: str
    skills_required: tuple[str, ...]
    difficulty: Difficulty
    learning_value: LearningValue
    reasoning: str

    def __post_init__(self) -> None:
        self._validate_choice(
            "problem_type", self.problem_type, _ALLOWED_PROBLEM_TYPES
        )
        self._validate_choice("difficulty", self.difficulty, _ALLOWED_DIFFICULTIES)
        self._validate_choice(
            "learning_value", self.learning_value, _ALLOWED_LEARNING_VALUES
        )

        if not isinstance(self.domain, str):
            raise TypeError("domain must be a string")
        if not isinstance(self.reasoning, str):
            raise TypeError("reasoning must be a string")
        if isinstance(self.skills_required, str):
            raise TypeError("skills_required must be a collection of strings")

        try:
            skills = tuple(self.skills_required)
        except TypeError as error:
            raise TypeError(
                "skills_required must be a collection of strings"
            ) from error
        if not all(isinstance(skill, str) for skill in skills):
            raise TypeError("skills_required must contain only strings")

        object.__setattr__(self, "skills_required", skills)

    @staticmethod
    def _validate_choice(
        field_name: str,
        value: str,
        allowed_values: frozenset[str],
    ) -> None:
        if value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            raise ValueError(f"{field_name} must be one of: {allowed}")
