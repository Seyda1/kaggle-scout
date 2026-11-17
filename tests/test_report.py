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


def competition(title: str) -> Competition:
    return Competition(
        ref=title,
        title=title,
        deadline=datetime(2026, 12, 31),
        team_count=1,
        url=f"https://www.kaggle.com/competitions/{title.lower()}",
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


def test_report_shows_start_date_when_known() -> None:
    started = Competition(
        ref="new",
        title="New",
        deadline=datetime(2026, 11, 30),
        team_count=1,
        start_date=datetime(2026, 11, 1, 9, 0),
    )
    items = rank_competitions(profile(), [(started, interpretation())])

    report = build_report(items, report_date=REPORT_DATE)

    assert "started 1 Nov 2026 | deadline 30 Nov 2026" in report.text
    assert "started 1 Nov 2026 | deadline 30 Nov 2026" in report.html
    assert "started" not in build_report(ranked(), report_date=REPORT_DATE).text


def test_matched_goals_are_shown_after_the_learning_reason() -> None:
    items = rank_competitions(
        profile(),
        [
            (
                competition("Goal"),
                interpretation(matched_goals=("practice", "learn <vision>")),
            ),
            (competition("NoGoal"), interpretation(learning_value="low")),
        ],
    )

    report = build_report(items, report_date=REPORT_DATE)

    assert "High learning value (practice, learn <vision>)" in report.text
    assert "Low learning value\n" in report.text
    assert "High learning value (practice, learn &lt;vision&gt;)" in report.html


def test_skill_breakdown_is_shown_after_the_skill_reason() -> None:
    items = rank_competitions(
        profile(),
        [
            (
                competition("Skills"),
                interpretation(
                    skills_you_have=("python",),
                    skills_to_learn=("deep learning",),
                ),
            ),
        ],
    )

    report = build_report(items, report_date=REPORT_DATE)

    assert (
        "Partial skill match (you have: python; you'd learn: deep learning)"
        in report.text
    )


def test_each_section_lists_newest_start_date_first() -> None:
    def dated(title: str, start: datetime | None) -> Competition:
        return Competition(
            ref=title,
            title=title,
            deadline=datetime(2030, 1, 1),
            team_count=1,
            start_date=start,
        )

    items = rank_competitions(
        profile(),
        [
            (dated("Old high", datetime(2012, 9, 28)), interpretation()),
            (dated("Undated", None), interpretation()),
            (dated("Newest", datetime(2026, 11, 9)), interpretation(learning_value="medium")),
            (dated("Same day A", datetime(2026, 11, 1)), interpretation()),
            (dated("Same day B", datetime(2026, 11, 1)), interpretation(learning_value="medium")),
        ],
    )

    text = build_report(items, report_date=REPORT_DATE).text
    order = ["Newest", "Same day A", "Same day B", "Old high", "Undated"]
    positions = [text.index(f"  {title}\n") for title in order]
    assert positions == sorted(positions)


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


def test_new_only_report_counts_new_and_skipped_competitions() -> None:
    report = build_report(
        ranked(),
        report_date=REPORT_DATE,
        new_only=True,
        skipped=18,
    )

    assert report.subject == "Kaggle Scout: 3 new for you (9 Nov 2026)"
    assert (
        "3 new for you. 18 competitions you already received were skipped."
        in report.text
    )
    assert "RECOMMENDED (1)" in report.text


def test_new_only_report_says_nothing_new_today() -> None:
    report = build_report([], report_date=REPORT_DATE, new_only=True, skipped=1)

    assert report.subject == "Kaggle Scout: nothing new today (9 Nov 2026)"
    assert (
        "Nothing new today. 1 competition you already received was skipped."
        in report.text
    )
    assert "Nothing new today." in report.html


def test_report_shows_change_notes() -> None:
    report = build_report(
        ranked(),
        report_date=REPORT_DATE,
        new_only=True,
        notes=("Your profile changed.",),
    )

    assert "Note: Your profile changed." in report.text
    assert "<em>Note: Your profile changed.</em>" in report.html


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
