"""Format ranked competitions as a daily email report."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from html import escape

from kaggle_scout.ranking import RankedRecommendation
from kaggle_scout.recommendation_decision import Decision


_SECTIONS: tuple[tuple[Decision, str], ...] = (
    ("recommended", "Recommended"),
    ("maybe", "Maybe"),
    ("not_recommended", "Not recommended"),
)


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
    interpretation = item.interpretation
    skill = explanation.skill_reason
    if interpretation.skills_you_have or interpretation.skills_to_learn:
        have = ", ".join(interpretation.skills_you_have) or "none"
        learn = ", ".join(interpretation.skills_to_learn) or "none"
        skill = f"{skill} (you have: {have}; you'd learn: {learn})"
    learning = explanation.learning_value_reason
    if interpretation.matched_goals:
        learning = f"{learning} ({', '.join(interpretation.matched_goals)})"
    return "; ".join(
        (
            skill,
            explanation.difficulty_reason,
            explanation.interest_reason,
            learning,
        )
    )


def _facts_line(item: RankedRecommendation) -> str:
    interpretation = item.interpretation
    competition = item.competition
    dates = f"deadline {_format_date(competition.deadline.date())}"
    if competition.start_date is not None:
        dates = f"started {_format_date(competition.start_date.date())} | {dates}"
    return (
        f"{interpretation.problem_type} | {interpretation.difficulty}"
        f" | {interpretation.domain} | {dates}"
    )


def _newest_first(items: list[RankedRecommendation]) -> list[RankedRecommendation]:
    # Stable sort keeps the incoming score order for equal start dates.
    dated = [item for item in items if item.competition.start_date is not None]
    undated = [item for item in items if item.competition.start_date is None]
    dated.sort(key=lambda item: item.competition.start_date, reverse=True)
    return dated + undated


def _group(
    ranked: Sequence[RankedRecommendation],
) -> list[tuple[str, list[RankedRecommendation]]]:
    return [
        (
            label,
            _newest_first(
                [item for item in ranked if item.decision.decision == decision]
            ),
        )
        for decision, label in _SECTIONS
    ]


def _summary_line(ranked_count: int, *, new_only: bool, skipped: int) -> str:
    if not new_only:
        return f"{ranked_count} active competitions ranked against your profile."
    noun, verb = ("competition", "was") if skipped == 1 else ("competitions", "were")
    already = f" {skipped} {noun} you already received {verb} skipped." if skipped else ""
    if ranked_count == 0:
        return f"Nothing new today.{already}"
    return f"{ranked_count} new for you.{already}"


def _subject(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    *,
    new_only: bool,
) -> str:
    day = _format_date(report_date)
    if not ranked and failures:
        return f"Kaggle Scout: no competitions analyzed ({day})"
    if new_only:
        if not ranked:
            return f"Kaggle Scout: nothing new today ({day})"
        return f"Kaggle Scout: {len(ranked)} new for you ({day})"
    count = sum(1 for item in ranked if item.decision.decision == "recommended")
    noun = "competition" if count == 1 else "competitions"
    return f"Kaggle Scout: {count} recommended {noun} ({day})"


def _text_body(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    summary: str,
    notes: Sequence[str],
) -> str:
    lines = [f"Kaggle Scout daily report - {_format_date(report_date)}", summary]
    if notes:
        lines.append("")
        lines += [f"Note: {note}" for note in notes]
    for label, items in _group(ranked):
        if not items:
            continue
        lines += ["", f"{label.upper()} ({len(items)})", ""]
        for item in items:
            lines.append(f"{item.score.total_score:.0%}  {item.competition.title}")
            lines.append(f"     {_facts_line(item)}")
            lines.append(f"     {_signal_line(item)}")
            lines.append(f"     {_reason_line(item)}")
            if item.competition.url:
                lines.append(f"     {item.competition.url}")
            lines.append("")
    if failures:
        lines += ["", f"COULD NOT ANALYZE ({len(failures)})", ""]
        lines += [f"- {failure}" for failure in failures]
    return "\n".join(lines).rstrip() + "\n"


def _html_item(item: RankedRecommendation) -> str:
    title = escape(item.competition.title)
    if item.competition.url:
        title = f'<a href="{escape(item.competition.url)}">{title}</a>'
    return (
        "<li style=\"margin-bottom:12px\">"
        f"<strong>{item.score.total_score:.0%}</strong> {title}<br>"
        f"<small>{escape(_facts_line(item))}<br>"
        f"{escape(_signal_line(item))}<br>"
        f"{escape(_reason_line(item))}</small>"
        "</li>"
    )


def _html_body(
    ranked: Sequence[RankedRecommendation],
    failures: Sequence[str],
    report_date: date,
    summary: str,
    notes: Sequence[str],
) -> str:
    parts = [
        "<html><body style=\"font-family:Segoe UI,Arial,sans-serif\">",
        f"<h2>Kaggle Scout daily report - {_format_date(report_date)}</h2>",
        f"<p>{escape(summary)}</p>",
    ]
    parts += [f"<p><em>Note: {escape(note)}</em></p>" for note in notes]
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
    new_only: bool = False,
    skipped: int = 0,
    notes: Sequence[str] = (),
) -> EmailReport:
    """Group competitions by decision, newest start date first in each group.

    With ``new_only``, the report describes only competitions not sent before;
    ``skipped`` counts the active ones left out because they were already sent.
    """
    summary = _summary_line(len(ranked), new_only=new_only, skipped=skipped)
    return EmailReport(
        subject=_subject(ranked, failures, report_date, new_only=new_only),
        text=_text_body(ranked, failures, report_date, summary, notes),
        html=_html_body(ranked, failures, report_date, summary, notes),
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
