"""Command-line entry point for the daily report."""

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from kaggle_scout.analysis import LLMCompetitionAnalyzer, OllamaCompetitionProvider
from kaggle_scout.daily_report import run_daily_report
from kaggle_scout.discovery import KaggleDiscovery
from kaggle_scout.emailer import GmailSettings, send_report
from kaggle_scout.env_file import load_env_file
from kaggle_scout.profile_loader import load_user_profile
from kaggle_scout.report import EmailReport, build_failure_report, build_report
from kaggle_scout.seen_store import DEFAULT_SEEN_PATH, SeenStore, SetupFingerprint


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
SEEN_PATH = DEFAULT_SEEN_PATH


@dataclass(frozen=True, slots=True)
class _Run:
    report: EmailReport
    succeeded: bool
    memory: SeenStore | None = None


def _build_report(report_date: date, *, show_all: bool) -> _Run:
    # Kaggle deadlines are naive UTC datetimes.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    step = "loading your profile"
    try:
        profile = load_user_profile()
        provider = OllamaCompetitionProvider(
            timeout=180.0,
            learning_goals=profile.learning_goals,
            skills=profile.skills,
        )
        fingerprint = SetupFingerprint.of(
            profile,
            model=provider.model,
            instructions=provider.instructions,
            options=provider.OPTIONS,
        )
        step = "reading the list of competitions already sent"
        memory = SeenStore.load(SEEN_PATH)
        step = "discovering and analyzing Kaggle competitions"
        result = run_daily_report(
            profile=profile,
            source=KaggleDiscovery(),
            interpreter=LLMCompetitionAnalyzer(provider),
            reference_time=now,
            include=(
                (lambda competition: True)
                if show_all
                else (
                    lambda competition: not memory.is_current(
                        competition.ref, fingerprint
                    )
                )
            ),
        )
    except Exception as error:
        return _Run(build_failure_report(step, error, report_date=report_date), False)

    notes = () if show_all else memory.change_notes(result.active_refs, fingerprint)
    memory.record(result.ranked, fingerprint=fingerprint, shown_on=report_date)
    memory.prune(result.active_refs)

    report = build_report(
        result.ranked,
        report_date=report_date,
        failures=result.failures,
        new_only=not show_all,
        skipped=result.skipped,
        notes=notes,
    )
    succeeded = bool(result.ranked) or not result.failures
    return _Run(report, succeeded, memory)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rank active Kaggle competitions against your profile."
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="also send the report through Gmail (settings come from .env)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include competitions already sent in earlier reports",
    )
    args = parser.parse_args(argv)

    load_env_file(ENV_PATH)
    run = _build_report(date.today(), show_all=args.all)
    print(run.report.subject)
    print()
    print(run.report.text)

    if args.email:
        try:
            send_report(GmailSettings.from_env(os.environ), run.report)
        except Exception as error:
            print(f"Email not sent: {type(error).__name__}: {error}", file=sys.stderr)
            return 1
        print("Report emailed.")
        # Only emailed competitions count as seen, so a failed send hides nothing.
        if run.memory is not None:
            try:
                run.memory.save(SEEN_PATH)
            except OSError as error:
                print(
                    f"Could not save sent competitions: {type(error).__name__}: {error}",
                    file=sys.stderr,
                )
                return 1

    return 0 if run.succeeded else 1
