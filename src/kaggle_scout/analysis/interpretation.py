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
    matched_goals: tuple[str, ...] = ()
    skills_you_have: tuple[str, ...] = ()
    skills_to_learn: tuple[str, ...] = ()

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

        object.__setattr__(
            self,
            "skills_required",
            self._string_tuple("skills_required", self.skills_required),
        )
        object.__setattr__(
            self,
            "matched_goals",
            self._string_tuple("matched_goals", self.matched_goals),
        )
        object.__setattr__(
            self,
            "skills_you_have",
            self._string_tuple("skills_you_have", self.skills_you_have),
        )
        object.__setattr__(
            self,
            "skills_to_learn",
            self._string_tuple("skills_to_learn", self.skills_to_learn),
        )

    @staticmethod
    def _string_tuple(field_name: str, values: object) -> tuple[str, ...]:
        if isinstance(values, str):
            raise TypeError(f"{field_name} must be a collection of strings")
        try:
            items = tuple(values)  # type: ignore[arg-type]
        except TypeError as error:
            raise TypeError(
                f"{field_name} must be a collection of strings"
            ) from error
        if not all(isinstance(item, str) for item in items):
            raise TypeError(f"{field_name} must contain only strings")
        return items

    @staticmethod
    def _validate_choice(
        field_name: str,
        value: str,
        allowed_values: frozenset[str],
    ) -> None:
        if value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            raise ValueError(f"{field_name} must be one of: {allowed}")
