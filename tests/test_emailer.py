"""Tests for Gmail settings and sending, using a fake SMTP client."""

import pytest

from kaggle_scout.emailer import (
    EmailConfigError,
    GmailSettings,
    build_message,
    send_report,
)
from kaggle_scout.report import EmailReport


REPORT = EmailReport(subject="Subject", text="Plain body\n", html="<p>Html body</p>")


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host: str, port: int, *, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logins: list[tuple[str, str]] = []
        self.sent: list[object] = []
        self.closed = False
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.closed = True

    def login(self, user: str, password: str) -> None:
        self.logins.append((user, password))

    def send_message(self, message: object) -> None:
        self.sent.append(message)


def settings() -> GmailSettings:
    return GmailSettings(
        address="sender@gmail.com",
        app_password="abcdabcdabcdabcd",
        recipient="reader@gmail.com",
    )


def test_from_env_reads_values_and_strips_password_spaces() -> None:
    loaded = GmailSettings.from_env(
        {
            "GMAIL_ADDRESS": " sender@gmail.com ",
            "GMAIL_APP_PASSWORD": "abcd efgh ijkl mnop",
            "REPORT_RECIPIENT": "reader@gmail.com",
        }
    )

    assert loaded.address == "sender@gmail.com"
    assert loaded.app_password == "abcdefghijklmnop"
    assert loaded.recipient == "reader@gmail.com"


def test_from_env_defaults_recipient_to_sender() -> None:
    loaded = GmailSettings.from_env(
        {"GMAIL_ADDRESS": "sender@gmail.com", "GMAIL_APP_PASSWORD": "secret"}
    )

    assert loaded.recipient == "sender@gmail.com"


def test_from_env_names_missing_settings_without_values() -> None:
    with pytest.raises(EmailConfigError, match="GMAIL_ADDRESS, GMAIL_APP_PASSWORD"):
        GmailSettings.from_env({})


def test_settings_repr_hides_app_password() -> None:
    assert "abcdabcdabcdabcd" not in repr(settings())


def test_build_message_has_text_and_html_parts() -> None:
    message = build_message(settings(), REPORT)

    assert message["Subject"] == "Subject"
    assert message["From"] == "sender@gmail.com"
    assert message["To"] == "reader@gmail.com"
    assert message.get_body(("plain",)).get_content() == "Plain body\n"
    assert "Html body" in message.get_body(("html",)).get_content()


def test_send_report_logs_in_and_sends_over_ssl_port() -> None:
    FakeSMTP.instances = []

    send_report(settings(), REPORT, smtp_factory=FakeSMTP)

    (smtp,) = FakeSMTP.instances
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 465)
    assert smtp.logins == [("sender@gmail.com", "abcdabcdabcdabcd")]
    assert len(smtp.sent) == 1
    assert smtp.closed
