"""Tests for the daily report command, with all external calls replaced."""

from datetime import timedelta

import pytest

from kaggle_scout import cli
from kaggle_scout.daily_report import DailyReportResult
from kaggle_scout.report import EmailReport


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_env_file", lambda path: None)
    monkeypatch.setattr(cli, "load_user_profile", lambda: object())
    monkeypatch.setattr(cli, "KaggleDiscovery", lambda: object())
    monkeypatch.setattr(cli, "OllamaCompetitionProvider", lambda **kwargs: object())
    monkeypatch.setattr(cli, "LLMCompetitionAnalyzer", lambda provider: object())
    for name in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "REPORT_RECIPIENT"):
        monkeypatch.delenv(name, raising=False)


def fake_run(ranked: list[object], failures: tuple[str, ...] = ()):
    def run(**kwargs: object) -> DailyReportResult:
        return DailyReportResult(ranked=ranked, failures=failures)

    return run


def fake_build_report(ranked, **kwargs) -> EmailReport:
    return EmailReport(subject="Daily subject", text="Daily body\n", html="<p></p>")


def test_main_prints_report_without_sending(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sent: list[object] = []
    monkeypatch.setattr(cli, "run_daily_report", fake_run([object()]))
    monkeypatch.setattr(cli, "build_report", fake_build_report)
    monkeypatch.setattr(cli, "send_report", lambda *args: sent.append(args))

    assert cli.main([]) == 0

    output = capsys.readouterr().out
    assert "Daily subject" in output
    assert "Daily body" in output
    assert sent == []


def test_main_emails_report_with_env_settings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sent: list[tuple[object, EmailReport]] = []
    monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setattr(cli, "run_daily_report", fake_run([object()]))
    monkeypatch.setattr(cli, "build_report", fake_build_report)
    monkeypatch.setattr(
        cli, "send_report", lambda settings, report: sent.append((settings, report))
    )

    assert cli.main(["--email"]) == 0

    (settings, report), = sent
    assert settings.recipient == "sender@gmail.com"
    assert report.subject == "Daily subject"
    output = capsys.readouterr().out
    assert "Report emailed." in output
    assert "secret" not in output


def test_main_sends_failure_report_when_a_step_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_profile() -> object:
        raise FileNotFoundError("profile missing")

    monkeypatch.setattr(cli, "load_user_profile", broken_profile)

    assert cli.main([]) == 1

    output = capsys.readouterr().out
    assert "report failed" in output
    assert "The run stopped while loading your profile." in output


def test_main_returns_error_when_email_settings_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "run_daily_report", fake_run([object()]))
    monkeypatch.setattr(cli, "build_report", fake_build_report)

    assert cli.main(["--email"]) == 1

    assert "Email not sent: EmailConfigError" in capsys.readouterr().err


def test_main_marks_competitions_launched_in_the_last_24_hours(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def run(**kwargs: object) -> DailyReportResult:
        calls.append({"reference_time": kwargs["reference_time"]})
        return DailyReportResult(ranked=[object()], failures=())

    def build(ranked, **kwargs) -> EmailReport:
        calls.append({"new_since": kwargs["new_since"]})
        return fake_build_report(ranked)

    monkeypatch.setattr(cli, "run_daily_report", run)
    monkeypatch.setattr(cli, "build_report", build)

    assert cli.main([]) == 0

    reference_time = calls[0]["reference_time"]
    assert reference_time.tzinfo is None
    assert reference_time - calls[1]["new_since"] == timedelta(hours=24)


def test_main_returns_error_when_nothing_was_analyzed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "run_daily_report", fake_run([], ("A: Error: x",)))
    monkeypatch.setattr(cli, "build_report", fake_build_report)

    assert cli.main([]) == 1
