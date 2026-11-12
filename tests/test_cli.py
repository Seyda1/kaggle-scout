"""Tests for the daily report command, with all external calls replaced."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from kaggle_scout import cli
from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.user_profile import UserProfile


def make_profile(skills: tuple[str, ...] = ("python",)) -> UserProfile:
    return UserProfile(
        skills=skills,
        experience_level="intermediate",
        interests=("classification",),
        preferred_difficulty_levels=("intermediate",),
        learning_goals=("practice",),
    )


def competition(ref: str) -> Competition:
    return Competition(
        ref=ref,
        title=f"Competition {ref}",
        deadline=datetime(2099, 1, 1),
        team_count=1,
    )


class FakeSource:
    def __init__(self) -> None:
        self.competitions = [competition("a"), competition("b")]

    def discover_active(self, *, reference_time: datetime) -> list[Competition]:
        return list(self.competitions)

    def load_overview(self, item: Competition) -> Competition:
        return item


class FakeInterpreter:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.analyzed: list[str] = []

    def analyze(self, item: Competition) -> CompetitionInterpretation:
        self.analyzed.append(item.ref)
        if self.fail:
            raise TimeoutError("model timed out")
        return CompetitionInterpretation(
            problem_type="classification",
            domain="retail",
            skills_required=("python",),
            difficulty="intermediate",
            learning_value="high",
            reasoning="Example.",
        )


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> SimpleNamespace:
    state = SimpleNamespace(
        profile=make_profile(),
        source=FakeSource(),
        interpreter=FakeInterpreter(),
        provider=SimpleNamespace(model="qwen3:14b", INSTRUCTIONS="Analyze."),
        sent=[],
        seen_path=tmp_path / "seen.json",
    )
    monkeypatch.setattr(cli, "load_env_file", lambda path: None)
    monkeypatch.setattr(cli, "SEEN_PATH", state.seen_path)
    monkeypatch.setattr(cli, "load_user_profile", lambda: state.profile)
    monkeypatch.setattr(cli, "KaggleDiscovery", lambda: state.source)
    monkeypatch.setattr(
        cli, "OllamaCompetitionProvider", lambda **kwargs: state.provider
    )
    monkeypatch.setattr(cli, "LLMCompetitionAnalyzer", lambda provider: state.interpreter)
    monkeypatch.setattr(
        cli, "send_report", lambda settings, report: state.sent.append((settings, report))
    )
    monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.delenv("REPORT_RECIPIENT", raising=False)
    return state


def test_print_only_does_not_send_or_remember(
    env: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([]) == 0

    output = capsys.readouterr().out
    assert "2 new for you" in output
    assert env.sent == []
    assert not env.seen_path.exists()


def test_email_remembers_sent_competitions_and_skips_them_next_time(
    env: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["--email"]) == 0
    assert env.seen_path.exists()
    assert env.interpreter.analyzed == ["a", "b"]

    env.source.competitions.append(competition("c"))
    env.interpreter.analyzed.clear()
    assert cli.main(["--email"]) == 0

    assert env.interpreter.analyzed == ["c"]
    second = env.sent[-1][1]
    assert second.subject.startswith("Kaggle Scout: 1 new for you")
    assert "Competition c" in second.text
    assert "Competition a" not in second.text
    assert "2 competitions you already received were skipped." in second.text
    output = capsys.readouterr().out
    assert "Report emailed." in output
    assert "secret" not in output


def test_nothing_new_sends_short_report(env: SimpleNamespace) -> None:
    cli.main(["--email"])
    env.interpreter.analyzed.clear()

    assert cli.main(["--email"]) == 0

    report = env.sent[-1][1]
    assert report.subject.startswith("Kaggle Scout: nothing new today")
    assert "Nothing new today." in report.text
    assert env.interpreter.analyzed == []


def test_profile_change_shows_sent_competitions_again_with_note(
    env: SimpleNamespace,
) -> None:
    cli.main(["--email"])
    env.profile = make_profile(skills=("python", "sql"))

    assert cli.main(["--email"]) == 0

    report = env.sent[-1][1]
    assert report.subject.startswith("Kaggle Scout: 2 new for you")
    assert "Your profile changed since the last report" in report.text
    assert "analysis model or prompt changed" not in report.text


def test_model_or_prompt_change_analyzes_sent_competitions_again(
    env: SimpleNamespace,
) -> None:
    cli.main(["--email"])
    env.provider = SimpleNamespace(model="qwen3:14b", INSTRUCTIONS="Analyze better.")
    env.interpreter.analyzed.clear()

    assert cli.main(["--email"]) == 0

    assert env.interpreter.analyzed == ["a", "b"]
    assert "analysis model or prompt changed" in env.sent[-1][1].text


def test_all_flag_includes_sent_competitions(env: SimpleNamespace) -> None:
    cli.main(["--email"])

    assert cli.main(["--all"]) == 0

    assert env.interpreter.analyzed[-2:] == ["a", "b"]


def test_failed_send_does_not_remember(
    env: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_send(settings: object, report: object) -> None:
        raise TimeoutError("smtp timed out")

    monkeypatch.setattr(cli, "send_report", broken_send)

    assert cli.main(["--email"]) == 1

    assert "Email not sent: TimeoutError" in capsys.readouterr().err
    assert not env.seen_path.exists()


def test_closed_competitions_are_forgotten(env: SimpleNamespace) -> None:
    cli.main(["--email"])
    env.source.competitions = [competition("b")]

    cli.main(["--email"])

    assert '"a"' not in env.seen_path.read_text(encoding="utf-8")
    assert '"b"' in env.seen_path.read_text(encoding="utf-8")


def test_failure_report_when_a_step_fails(
    env: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_profile() -> UserProfile:
        raise FileNotFoundError("profile missing")

    monkeypatch.setattr(cli, "load_user_profile", broken_profile)

    assert cli.main(["--email"]) == 1

    output = capsys.readouterr().out
    assert "report failed" in output
    assert "The run stopped while loading your profile." in output
    assert not env.seen_path.exists()


def test_missing_email_settings_return_error(
    env: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("GMAIL_ADDRESS")
    monkeypatch.delenv("GMAIL_APP_PASSWORD")

    assert cli.main(["--email"]) == 1

    assert "Email not sent: EmailConfigError" in capsys.readouterr().err


def test_returns_error_when_nothing_could_be_analyzed(env: SimpleNamespace) -> None:
    env.interpreter.fail = True

    assert cli.main([]) == 1
