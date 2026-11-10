"""Command-line entry point for the daily report."""

import argparse
import os
import sys
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from kaggle_scout.analysis import LLMCompetitionAnalyzer, OllamaCompetitionProvider
from kaggle_scout.daily_report import run_daily_report
from kaggle_scout.discovery import KaggleDiscovery
from kaggle_scout.emailer import GmailSettings, send_report
from kaggle_scout.env_file import load_env_file
from kaggle_scout.profile_loader import load_user_profile
from kaggle_scout.report import EmailReport, build_failure_report, build_report


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
TODAY_WINDOW = timedelta(hours=24)


def _build_report(report_date: date) -> tuple[EmailReport, bool]:
    # Kaggle deadlines and launch dates are naive UTC datetimes.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    step = "loading your profile"
    try:
        profile = load_user_profile()
        step = "discovering and analyzing Kaggle competitions"
        result = run_daily_report(
            profile=profile,
            source=KaggleDiscovery(),
            interpreter=LLMCompetitionAnalyzer(
                OllamaCompetitionProvider(timeout=180.0)
            ),
            reference_time=now,
        )
    except Exception as error:
        return build_failure_report(step, error, report_date=report_date), False

    report = build_report(
        result.ranked,
        report_date=report_date,
        failures=result.failures,
        new_since=now - TODAY_WINDOW,
    )
    return report, bool(result.ranked)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rank active Kaggle competitions against your profile."
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="also send the report through Gmail (settings come from .env)",
    )
    args = parser.parse_args(argv)

    load_env_file(ENV_PATH)
    report, succeeded = _build_report(date.today())
    print(report.subject)
    print()
    print(report.text)

    if args.email:
        try:
            send_report(GmailSettings.from_env(os.environ), report)
        except Exception as error:
            print(f"Email not sent: {type(error).__name__}: {error}", file=sys.stderr)
            return 1
        print("Report emailed.")

    return 0 if succeeded else 1
