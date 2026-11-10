"""Tests for the daily email report formatting."""

from datetime import date, datetime

from kaggle_scout.analysis import CompetitionInterpretation
from kaggle_scout.competition import Competition
from kaggle_scout.ranking import rank_competitions
from kaggle_scout.report import build_failure_report, build_report
from kaggle_scout.user_profile import UserProfile


REPORT_DATE = date(2026, 11, 9)


def profile() -> UserProfile:
    return UserProfile(
        skills=("python",),
        experience_level="intermediate",
        interests=("classification",),
        preferred_difficulty_levels=("intermediate",),
        learning_goals=("practice",),
    )


def competition(title: str, launch_date: datetime | None = None) -> Competition:
    return Competition(
        ref=title,
        title=title,
        deadline=datetime(2026, 12, 31),
        team_count=1,
        url=f"https://www.kaggle.com/competitions/{title.lower()}",
        launch_date=launch_date,
    )


def interpretation(**overrides: object) -> CompetitionInterpretation:
    values = {
        "problem_type": "classification",
        "domain": "retail",
        "skills_required": ("python",),
        "difficulty": "intermediate",
        "learning_value": "high",
        "reasoning": "A classification task.",
    }
    values.update(overrides)
    return CompetitionInterpretation(**values)


def ranked():
    return rank_competitions(
        profile(),
        [
            (competition("Strong"), interpretation()),
            (
                competition("Middle"),
                interpretation(problem_type="regression", learning_value="medium"),
            ),
            (
                competition("Weak"),
                interpretation(
                    problem_type="regression",
                    skills_required=("rust",),
                    difficulty="advanced",
                    learning_value="low",
                ),
            ),
        ],
    )


def test_report_groups_competitions_by_decision_in_score_order() -> None:
    report = build_report(ranked(), report_date=REPORT_DATE)

    text = report.text
    assert report.subject == "Kaggle Scout: 1 recommended competition (9 Nov 2026)"
    assert text.index("RECOMMENDED (1)") < text.index("Strong")
    assert text.index("Strong") < text.index("MAYBE (1)") < text.index("Middle")
    assert text.index("Middle") < text.index("NOT RECOMMENDED (1)")
    assert text.index("NOT RECOMMENDED (1)") < text.index("Weak")
    assert "https://www.kaggle.com/competitions/strong" in text
    assert "skill 1.00 · difficulty 1.00 · interest 1.00 · learning 1.00" in text


def test_report_lists_failures_and_skips_empty_sections() -> None:
    items = [item for item in ranked() if item.competition.title == "Strong"]

    report = build_report(
        items,
        report_date=REPORT_DATE,
        failures=("Broken: TimeoutError: timed out",),
    )

    assert "MAYBE" not in report.text
    assert "COULD NOT ANALYZE (1)" in report.text
    assert "- Broken: TimeoutError: timed out" in report.text


def test_report_subject_flags_run_with_no_analyzed_competitions() -> None:
    report = build_report([], report_date=REPORT_DATE, failures=("A: Error: x",))

    assert report.subject == "Kaggle Scout: no competitions analyzed (9 Nov 2026)"


def test_html_report_escapes_titles_and_links_competitions() -> None:
    items = rank_competitions(
        profile(),
        [(competition("<Tag> & Co"), interpretation())],
    )

    html = build_report(items, report_date=REPORT_DATE).html

    assert "&lt;Tag&gt; &amp; Co" in html
    assert "<Tag>" not in html
    assert '<a href="https://www.kaggle.com/competitions/&lt;tag&gt; &amp; co">' in html


NEW_SINCE = datetime(2026, 11, 8, 6, 30)


def ranked_with_launches():
    return rank_competitions(
        profile(),
        [
            (competition("Fresh", datetime(2026, 11, 8, 20, 0)), interpretation()),
            (
                competition("Edge", NEW_SINCE),
                interpretation(problem_type="regression", learning_value="medium"),
            ),
            (competition("Older", datetime(2026, 11, 8, 6, 29)), interpretation()),
            (competition("Undated"), interpretation()),
        ],
    )


def test_today_section_lists_launches_since_cutoff_with_decision() -> None:
    report = build_report(
        ranked_with_launches(),
        report_date=REPORT_DATE,
        new_since=NEW_SINCE,
    )

    text = report.text
    today = text[text.index("TODAY'S COMPETITIONS (2)") : text.index("RECOMMENDED (")]
    assert "Fresh  [Recommended]" in today
    assert "Edge  [Maybe]" in today
    assert "Older" not in today
    assert "Undated" not in today
    assert "launched 8 Nov 2026 | classification" in today
    assert report.subject == "Kaggle Scout: 3 recommended, 2 new today (9 Nov 2026)"


def test_today_competitions_also_stay_in_their_decision_section() -> None:
    text = build_report(
        ranked_with_launches(),
        report_date=REPORT_DATE,
        new_since=NEW_SINCE,
    ).text

    recommended = text[text.index("RECOMMENDED (3)") : text.index("MAYBE (1)")]
    assert "Fresh" in recommended
    assert "Edge" in text[text.index("MAYBE (1)") :]


def test_today_section_says_when_nothing_launched() -> None:
    report = build_report(
        ranked(),
        report_date=REPORT_DATE,
        new_since=NEW_SINCE,
    )

    assert "TODAY'S COMPETITIONS (0)" in report.text
    assert "No new competitions today." in report.text
    assert "No new competitions today." in report.html
    assert report.subject == "Kaggle Scout: 1 recommended competition (9 Nov 2026)"


def test_today_section_is_omitted_without_cutoff() -> None:
    report = build_report(ranked_with_launches(), report_date=REPORT_DATE)

    assert "TODAY'S COMPETITIONS" not in report.text
    assert "Today&#x27;s competitions" not in report.html


def test_html_today_section_lists_new_competitions() -> None:
    html = build_report(
        ranked_with_launches(),
        report_date=REPORT_DATE,
        new_since=NEW_SINCE,
    ).html

    assert "<h3>Today&#x27;s competitions (2)</h3>" in html
    assert "</a> [Recommended]" in html


def test_failure_report_names_step_and_error() -> None:
    report = build_failure_report(
        "loading your profile",
        FileNotFoundError("profile missing"),
        report_date=REPORT_DATE,
    )

    assert report.subject == "Kaggle Scout: report failed (9 Nov 2026)"
    assert "The run stopped while loading your profile." in report.text
    assert "FileNotFoundError: profile missing" in report.text
    assert "loading your profile" in report.html
