"""Application-level representation of a Kaggle competition."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Competition:
    """Competition metadata used by Kaggle Scout."""

    ref: str
    title: str
    deadline: datetime
    team_count: int
    description: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    category: str | None = None
    reward: str | None = None
    evaluation_metric: str | None = None
    date_created: datetime | None = None
    url: str | None = None
    overview: str | None = None
