"""Format ranked competitions as a daily email report."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from html import escape

from kaggle_scout.ranking import RankedRecommendation
from kaggle_scout.recommendation_decision import Decision


_SECTIONS: tuple[tuple[Decision, str], ...] = (
    ("recommended", "Recommended"),
    ("maybe", "Maybe"),
    ("not_recommended", "Not recommended"),
)
_DECISION_LABELS: dict[Decision, str] = dict(_SECTIONS)
_TODAY_LABEL = "Today's competitions"
_NO_NEW_TODAY = "No new competitions today."


@dataclass(frozen=True, slots=True)
class EmailReport:
    """Subject plus plain-text and HTML bodies for one email."""

    subject: str
    text: str
    html: str


def _format_date(value: date) -> str:
    return f"{value.day} {value:%b %Y}"


def _signal_line(item: RankedRecommendation) -> str:
    score = item.score
    return (
        f"skill {score.skill_match:.2f} · difficulty {score.difficulty_match:.2f}"
        f" · interest {score.interest_match:.2f}"
        f" · learning {score.learning_value:.2f}"
    )


def _reason_line(item: RankedRecommendation) -> str:
    explanation = item.explanation
    return "; ".join(
        (
            explanation.skill_reason,
            explanation.difficulty_reason,
            explanation.interest_reason,
            explanation.learning_value_reason,
        )
    )


def _facts_line(item: RankedRecommendation, *, show_launch: bool = False) -> str:
    interpretation = item.interpretation
    competition = item.competition
    facts = (
        f"{interpretation.problem_type} | {interpretation.difficulty}"
        f" | {interpretation.domain}"
        f" | deadline {_format_date(competition.deadline.date())}"
    )
    if show_launch and competition.launch_date is not None:
        facts = f"launched {_format_date(competition.launch_date.date())} | {facts}"
    return facts


def _group(
    ranked: Sequence[RankedRecommendation],
) -> list[tuple[str, list[RankedRecommendation]]]:
    return [
        (label, [item for item in ranked if item.decision.decision == decision])
        for decision, label in _SECTIONS
    ]


def _launched_since(
    ranked: Sequence[RankedRecommendation],
    new_since: datetime,
) -> list[RankedRecommendation]:
    return [
        item
        for item in ranked
        if item.competition.launch_date is not None
        and item.competition.launch_date >= new_since
    ]


def _subject(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    today: Sequence[RankedRecommendation] | None,
) -> str:
    day = _format_date(report_date)
    if not ranked and failures:
        return f"Kaggle Scout: no competitions analyzed ({day})"
    count = sum(1 for item in ranked if item.decision.decision == "recommended")
    noun = "competition" if count == 1 else "competitions"
    if today:
        return f"Kaggle Scout: {count} recommended, {len(today)} new today ({day})"
    return f"Kaggle Scout: {count} recommended {noun} ({day})"


def _text_item(item: RankedRecommendation, *, today: bool = False) -> list[str]:
    title = f"{item.score.total_score:.0%}  {item.competition.title}"
    if today:
        title = f"{title}  [{_DECISION_LABELS[item.decision.decision]}]"
    lines = [
        title,
        f"     {_facts_line(item, show_launch=today)}",
        f"     {_signal_line(item)}",
        f"     {_reason_line(item)}",
    ]
    if item.competition.url:
        lines.append(f"     {item.competition.url}")
    lines.append("")
    return lines


def _text_body(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    today: Sequence[RankedRecommendation] | None,
) -> str:
    lines = [
        f"Kaggle Scout daily report - {_format_date(report_date)}",
        f"{len(ranked)} active competitions ranked against your profile.",
    ]
    if today is not None:
        lines += ["", f"{_TODAY_LABEL.upper()} ({len(today)})", ""]
        if not today:
            lines.append(_NO_NEW_TODAY)
        for item in today:
            lines += _text_item(item, today=True)
    for label, items in _group(ranked):
        if not items:
            continue
        lines += ["", f"{label.upper()} ({len(items)})", ""]
        for item in items:
            lines += _text_item(item)
    if failures:
        lines += ["", f"COULD NOT ANALYZE ({len(failures)})", ""]
        lines += [f"- {failure}" for failure in failures]
    return "\n".join(lines).rstrip() + "\n"


def _html_item(item: RankedRecommendation, *, today: bool = False) -> str:
    title = escape(item.competition.title)
    if item.competition.url:
        title = f'<a href="{escape(item.competition.url)}">{title}</a>'
    if today:
        title = f"{title} [{escape(_DECISION_LABELS[item.decision.decision])}]"
    return (
        "<li style=\"margin-bottom:12px\">"
        f"<strong>{item.score.total_score:.0%}</strong> {title}<br>"
        f"<small>{escape(_facts_line(item, show_launch=today))}<br>"
        f"{escape(_signal_line(item))}<br>"
        f"{escape(_reason_line(item))}</small>"
        "</li>"
    )


def _html_body(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    today: Sequence[RankedRecommendation] | None,
) -> str:
    parts = [
        "<html><body style=\"font-family:Segoe UI,Arial,sans-serif\">",
        f"<h2>Kaggle Scout daily report - {_format_date(report_date)}</h2>",
        f"<p>{len(ranked)} active competitions ranked against your profile.</p>",
    ]
    if today is not None:
        parts.append(f"<h3>{escape(_TODAY_LABEL)} ({len(today)})</h3>")
        if today:
            parts.append("<ul>")
            parts += [_html_item(item, today=True) for item in today]
            parts.append("</ul>")
        else:
            parts.append(f"<p>{_NO_NEW_TODAY}</p>")
    for label, items in _group(ranked):
        if not items:
            continue
        parts.append(f"<h3>{label} ({len(items)})</h3><ul>")
        parts += [_html_item(item) for item in items]
        parts.append("</ul>")
    if failures:
        parts.append(f"<h3>Could not analyze ({len(failures)})</h3><ul>")
        parts += [f"<li>{escape(failure)}</li>" for failure in failures]
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


def build_report(
    ranked: Sequence[RankedRecommendation],
    *,
    report_date: date,
    failures: Sequence[str] = (),
    new_since: datetime | None = None,
) -> EmailReport:
    """Group ranked competitions by decision, keeping their score order.

    When ``new_since`` is given, competitions launched at or after it are also
    listed first under "Today's competitions".
    """
    today = None if new_since is None else _launched_since(ranked, new_since)
    return EmailReport(
        subject=_subject(ranked, failures, report_date, today),
        text=_text_body(ranked, failures, report_date, today),
        html=_html_body(ranked, failures, report_date, today),
    )


def build_failure_report(
    step: str,
    error: BaseException,
    *,
    report_date: date,
) -> EmailReport:
    """Describe which step stopped the daily run."""
    day = _format_date(report_date)
    detail = f"{type(error).__name__}: {error}"
    text = (
        f"Kaggle Scout daily report - {day}\n\n"
        f"The run stopped while {step}.\n"
        f"{detail}\n"
    )
    html = (
        "<html><body style=\"font-family:Segoe UI,Arial,sans-serif\">"
        f"<h2>Kaggle Scout daily report - {escape(day)}</h2>"
        f"<p>The run stopped while {escape(step)}.</p>"
        f"<pre>{escape(detail)}</pre>"
        "</body></html>"
    )
    return EmailReport(
        subject=f"Kaggle Scout: report failed ({day})",
        text=text,
        html=html,
    )
