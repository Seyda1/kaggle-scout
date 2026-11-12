"""Local memory of competitions already sent in a report."""

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from kaggle_scout.ranking import RankedRecommendation
from kaggle_scout.user_profile import UserProfile


_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEEN_PATH = _REPO_ROOT / "data" / "seen_competitions.json"

PROFILE_CHANGED_NOTE = (
    "Your profile changed since the last report, so competitions you saw "
    "before are shown again with updated scores."
)
ANALYSIS_CHANGED_NOTE = (
    "The analysis model or prompt changed since the last report, so "
    "competitions you saw before were analyzed again."
)


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class SetupFingerprint:
    """Hashes of the inputs that change what a report would say."""

    profile: str
    analysis: str

    @classmethod
    def of(
        cls,
        profile: UserProfile,
        *,
        model: str,
        instructions: str,
    ) -> "SetupFingerprint":
        return cls(
            profile=_short_hash(json.dumps(asdict(profile), sort_keys=True)),
            analysis=_short_hash(f"{model}\n{instructions}"),
        )


@dataclass(frozen=True, slots=True)
class SeenEntry:
    """What was sent about one competition, and under which setup."""

    shown_on: str
    score: float
    decision: str
    profile: str
    analysis: str


class SeenStore:
    """Competitions already sent, keyed by Kaggle ref."""

    def __init__(self, entries: dict[str, SeenEntry] | None = None) -> None:
        self._entries = dict(entries or {})

    @property
    def entries(self) -> dict[str, SeenEntry]:
        return dict(self._entries)

    @classmethod
    def load(cls, path: Path = DEFAULT_SEEN_PATH) -> "SeenStore":
        if not path.is_file():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Seen-competitions file is not valid JSON: {path}") from error
        competitions = raw.get("competitions", {}) if isinstance(raw, dict) else {}
        return cls({ref: SeenEntry(**entry) for ref, entry in competitions.items()})

    def save(self, path: Path = DEFAULT_SEEN_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "competitions": {
                ref: asdict(entry) for ref, entry in sorted(self._entries.items())
            }
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def is_current(self, ref: str, fingerprint: SetupFingerprint) -> bool:
        """True if the competition was already sent under this exact setup."""
        entry = self._entries.get(ref)
        return (
            entry is not None
            and entry.profile == fingerprint.profile
            and entry.analysis == fingerprint.analysis
        )

    def change_notes(
        self,
        refs: Iterable[str],
        fingerprint: SetupFingerprint,
    ) -> tuple[str, ...]:
        """Explain why previously sent competitions are being shown again."""
        seen = [self._entries[ref] for ref in refs if ref in self._entries]
        notes: list[str] = []
        if any(entry.profile != fingerprint.profile for entry in seen):
            notes.append(PROFILE_CHANGED_NOTE)
        if any(entry.analysis != fingerprint.analysis for entry in seen):
            notes.append(ANALYSIS_CHANGED_NOTE)
        return tuple(notes)

    def record(
        self,
        ranked: Iterable[RankedRecommendation],
        *,
        fingerprint: SetupFingerprint,
        shown_on: date,
    ) -> None:
        for item in ranked:
            self._entries[item.competition.ref] = SeenEntry(
                shown_on=shown_on.isoformat(),
                score=round(item.score.total_score, 4),
                decision=item.decision.decision,
                profile=fingerprint.profile,
                analysis=fingerprint.analysis,
            )

    def prune(self, active_refs: Iterable[str]) -> None:
        """Forget competitions that are no longer active."""
        active = set(active_refs)
        self._entries = {
            ref: entry for ref, entry in self._entries.items() if ref in active
        }
