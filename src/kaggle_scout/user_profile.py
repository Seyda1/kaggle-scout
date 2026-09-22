"""Application-level user profile for future competition matching."""

from dataclasses import dataclass
from typing import Literal, get_args


ExperienceLevel = Literal["beginner", "intermediate", "advanced", "unknown"]
PreferredDifficulty = Literal["beginner", "intermediate", "advanced"]

_ALLOWED_EXPERIENCE_LEVELS = frozenset(get_args(ExperienceLevel))
_ALLOWED_PREFERRED_DIFFICULTIES = frozenset(get_args(PreferredDifficulty))


@dataclass(frozen=True, slots=True)
class UserProfile:
    """Skills, interests, preferences, and learning goals for one user."""

    skills: tuple[str, ...]
    experience_level: ExperienceLevel
    interests: tuple[str, ...]
    preferred_difficulty_levels: tuple[PreferredDifficulty, ...]
    learning_goals: tuple[str, ...]

    def __post_init__(self) -> None:
        self._validate_choice(
            "experience_level",
            self.experience_level,
            _ALLOWED_EXPERIENCE_LEVELS,
        )
        object.__setattr__(
            self,
            "skills",
            self._validate_text_collection("skills", self.skills),
        )
        object.__setattr__(
            self,
            "interests",
            self._validate_text_collection("interests", self.interests),
        )
        object.__setattr__(
            self,
            "learning_goals",
            self._validate_text_collection("learning_goals", self.learning_goals),
        )

        difficulties = self._validate_text_collection(
            "preferred_difficulty_levels",
            self.preferred_difficulty_levels,
        )
        for difficulty in difficulties:
            self._validate_choice(
                "preferred_difficulty_levels",
                difficulty,
                _ALLOWED_PREFERRED_DIFFICULTIES,
            )
        object.__setattr__(self, "preferred_difficulty_levels", difficulties)

    @staticmethod
    def _validate_text_collection(
        field_name: str,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if isinstance(values, str):
            raise TypeError(f"{field_name} must be a collection of strings")
        try:
            items = tuple(values)
        except TypeError as error:
            raise TypeError(
                f"{field_name} must be a collection of strings"
            ) from error
        if not all(isinstance(item, str) for item in items):
            raise TypeError(f"{field_name} must contain only strings")
        if any(not item.strip() for item in items):
            raise ValueError(f"{field_name} must not contain blank strings")
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
