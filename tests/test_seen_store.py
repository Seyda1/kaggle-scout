"""Tests for the local memory of competitions already sent."""

from datetime import date, datetime
from pathlib import Path

import pytest

from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.ranking import rank_competitions
from kaggle_scout.seen_store import (
    ANALYSIS_CHANGED_NOTE,
    PROFILE_CHANGED_NOTE,
    SeenStore,
    SetupFingerprint,
)
from kaggle_scout.user_profile import UserProfile


def profile(skills: tuple[str, ...] = ("python",)) -> UserProfile:
    return UserProfile(
        skills=skills,
        experience_level="intermediate",
        interests=("classification",),
        preferred_difficulty_levels=("intermediate",),
        learning_goals=("practice",),
    )


def fingerprint(**overrides: object) -> SetupFingerprint:
    values = {"model": "qwen3:14b", "instructions": "Analyze."}
    values.update(overrides)
    return SetupFingerprint.of(values.pop("profile", profile()), **values)


def ranked(*refs: str):
    interpretation = CompetitionInterpretation(
        problem_type="classification",
        domain="retail",
        skills_required=("python",),
        difficulty="intermediate",
        learning_value="high",
        reasoning="Example.",
    )
    return rank_competitions(
        profile(),
        [
            (
                Competition(
                    ref=ref, title=ref, deadline=datetime(2099, 1, 1), team_count=1
                ),
                interpretation,
            )
            for ref in refs
        ],
    )


def test_fingerprint_changes_with_profile_model_or_instructions() -> None:
    base = fingerprint()

    assert fingerprint() == base
    assert fingerprint(profile=profile(("python", "sql"))).profile != base.profile
    assert fingerprint(profile=profile(("python", "sql"))).analysis == base.analysis
    assert fingerprint(model="qwen3:8b").analysis != base.analysis
    assert fingerprint(instructions="Analyze better.").analysis != base.analysis


def test_record_and_is_current() -> None:
    store = SeenStore()
    current = fingerprint()

    store.record(ranked("a"), fingerprint=current, shown_on=date(2026, 11, 10))

    assert store.is_current("a", current)
    assert not store.is_current("b", current)
    assert not store.is_current("a", fingerprint(model="qwen3:8b"))
    entry = store.entries["a"]
    assert entry.shown_on == "2026-11-10"
    assert entry.decision == "recommended"
    assert entry.score == 1.0


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "seen.json"
    store = SeenStore()
    store.record(ranked("b", "a"), fingerprint=fingerprint(), shown_on=date(2026, 11, 10))

    store.save(path)

    assert SeenStore.load(path).entries == store.entries


def test_load_missing_file_is_empty(tmp_path: Path) -> None:
    assert SeenStore.load(tmp_path / "missing.json").entries == {}


def test_load_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid JSON"):
        SeenStore.load(path)


def test_change_notes_explain_why_competitions_return() -> None:
    store = SeenStore()
    store.record(ranked("a"), fingerprint=fingerprint(), shown_on=date(2026, 11, 10))

    assert store.change_notes(["a"], fingerprint()) == ()
    assert store.change_notes(
        ["a"], fingerprint(profile=profile(("sql",)))
    ) == (PROFILE_CHANGED_NOTE,)
    assert store.change_notes(["a"], fingerprint(model="other")) == (
        ANALYSIS_CHANGED_NOTE,
    )
    assert store.change_notes(["b"], fingerprint(model="other")) == ()


def test_prune_forgets_inactive_competitions() -> None:
    store = SeenStore()
    store.record(ranked("a", "b"), fingerprint=fingerprint(), shown_on=date(2026, 11, 10))

    store.prune(["b", "c"])

    assert set(store.entries) == {"b"}
