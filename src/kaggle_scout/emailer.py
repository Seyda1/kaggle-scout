"""Send Kaggle Scout reports through Gmail SMTP."""

import smtplib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from email.message import EmailMessage

from kaggle_scout.report import EmailReport


GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465


class EmailConfigError(Exception):
    """Raised when Gmail settings are missing from the environment."""


@dataclass(frozen=True, slots=True)
class GmailSettings:
    """Sender account, app password, and report recipient."""

    address: str
    app_password: str = field(repr=False)
    recipient: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> "GmailSettings":
        address = environ.get("GMAIL_ADDRESS", "").strip()
        # Google displays app passwords in groups separated by spaces.
        app_password = "".join(environ.get("GMAIL_APP_PASSWORD", "").split())
        recipient = environ.get("REPORT_RECIPIENT", "").strip() or address

        missing = [
            name
            for name, value in (
                ("GMAIL_ADDRESS", address),
                ("GMAIL_APP_PASSWORD", app_password),
            )
            if not value
        ]
        if missing:
            raise EmailConfigError(
                f"Missing {', '.join(missing)} in .env; see .env.example"
            )
        return cls(address=address, app_password=app_password, recipient=recipient)


def build_message(settings: GmailSettings, report: EmailReport) -> EmailMessage:
    """Create a plain-text email with an HTML alternative."""
    message = EmailMessage()
    message["Subject"] = report.subject
    message["From"] = settings.address
    message["To"] = settings.recipient
    message.set_content(report.text)
    message.add_alternative(report.html, subtype="html")
    return message


def send_report(
    settings: GmailSettings,
    report: EmailReport,
    *,
    smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP_SSL,
    timeout: float = 30.0,
) -> None:
    """Log in to Gmail over SSL and send one report."""
    message = build_message(settings, report)
    with smtp_factory(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=timeout) as smtp:
        smtp.login(settings.address, settings.app_password)
        smtp.send_message(message)
