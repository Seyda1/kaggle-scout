"""Unit tests for the Kaggle discovery boundary."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from kaggle_scout.competition import Competition
from kaggle_scout.discovery import DiscoveryError, KaggleDiscovery


class FakeKaggleApi:
    """Small test double that records calls without contacting Kaggle."""

    def __init__(
        self,
        competitions: list[object] | None = None,
        *,
        responses: list[object] | None = None,
        error: Exception | None = None,
        pages: list[object] | None = None,
        page_error: Exception | None = None,
    ) -> None:
        self.responses = responses or [
            SimpleNamespace(
                competitions=competitions or [],
                next_page_token=None,
            )
        ]
        self.error = error
        self.pages = pages or []
        self.page_error = page_error
        self.authenticated = False
        self.list_arguments: dict[str, object] | None = None
        self.list_calls: list[dict[str, object]] = []
        self.page_calls: list[str] = []

    def authenticate(self) -> None:
        self.authenticated = True

    def competitions_list(self, **kwargs: object) -> object:
        if self.error is not None:
            raise self.error
        self.list_arguments = kwargs
        self.list_calls.append(kwargs)
        return self.responses.pop(0)

    def competition_list_pages(self, competition: str, page_name: str | None = None) -> list[object]:
        if self.page_error is not None:
            raise self.page_error
        self.page_calls.append(competition)
        if page_name is None:
            return list(self.pages)
        return [
            page
            for page in self.pages
            if getattr(page, "name", None) == page_name
        ]


def minimal_api_competition(ref: str) -> object:
    return SimpleNamespace(
        ref=ref,
        title=f"Competition {ref}",
        deadline=datetime(2026, 12, 31),
        team_count=0,
    )


def test_discovers_and_maps_complete_competition() -> None:
    deadline = datetime(2026, 12, 31, 23, 59)
    date_created = datetime(2026, 9, 1, 12, 30)
    api_competition = SimpleNamespace(
        ref="example-competition",
        title="Example Competition",
        description="Predict the target.",
        tags=[SimpleNamespace(name="tabular"), SimpleNamespace(name="regression")],
        deadline=deadline,
        category="Featured",
        reward="10,000 USD",
        evaluation_metric="RMSE",
        date_created=date_created,
        team_count=125,
        url="https://www.kaggle.com/competitions/example-competition",
    )

    competitions = KaggleDiscovery(FakeKaggleApi([api_competition])).discover()

    assert competitions == [
        Competition(
            ref="example-competition",
            title="Example Competition",
            description="Predict the target.",
            tags=("tabular", "regression"),
            deadline=deadline,
            category="Featured",
            reward="10,000 USD",
            evaluation_metric="RMSE",
            date_created=date_created,
            team_count=125,
            url="https://www.kaggle.com/competitions/example-competition",
        )
    ]


def test_maps_missing_optional_fields_safely() -> None:
    api_competition = SimpleNamespace(
        ref="minimal-competition",
        title="Minimal Competition",
        deadline=datetime(2026, 12, 31),
        description=None,
        tags=None,
        category="",
        reward=None,
        evaluation_metric=None,
        date_created=None,
        team_count=0,
        url="",
    )

    competition = KaggleDiscovery(FakeKaggleApi([api_competition])).discover()[0]

    assert competition.description is None
    assert competition.tags == ()
    assert competition.category is None
    assert competition.reward is None
    assert competition.evaluation_metric is None
    assert competition.date_created is None
    assert competition.team_count == 0
    assert competition.url is None


def test_requests_expected_page_configuration() -> None:
    api = FakeKaggleApi([])

    result = KaggleDiscovery(api).discover()

    assert api.authenticated is True
    assert api.list_arguments == {
        "sort_by": "recentlyCreated",
        "page_size": 20,
    }
    assert result == []


def test_follows_next_page_token() -> None:
    api = FakeKaggleApi(
        responses=[
            SimpleNamespace(
                competitions=[minimal_api_competition("one")],
                next_page_token="page-two",
            ),
            SimpleNamespace(
                competitions=[minimal_api_competition("two")],
                next_page_token=None,
            ),
        ]
    )

    competitions = KaggleDiscovery(api).discover()

    assert [competition.ref for competition in competitions] == ["one", "two"]
    assert len(api.list_calls) == 2
    assert "page_token" not in api.list_calls[0]
    assert api.list_calls[1]["page_token"] == "page-two"


def test_limit_caps_results_and_page_size() -> None:
    first_page = [minimal_api_competition(str(index)) for index in range(20)]
    second_page = [minimal_api_competition(str(index)) for index in range(20, 40)]
    api = FakeKaggleApi(
        responses=[
            SimpleNamespace(
                competitions=first_page,
                next_page_token="page-two",
            ),
            SimpleNamespace(
                competitions=second_page,
                next_page_token="page-three",
            ),
        ]
    )

    competitions = KaggleDiscovery(api).discover(limit=25)

    assert len(competitions) == 25
    assert [call["page_size"] for call in api.list_calls] == [20, 5]


def test_stops_when_no_next_page_token() -> None:
    api = FakeKaggleApi([minimal_api_competition("only")])

    competitions = KaggleDiscovery(api).discover(limit=50)

    assert [competition.ref for competition in competitions] == ["only"]
    assert len(api.list_calls) == 1


def test_passes_supported_filters() -> None:
    api = FakeKaggleApi([])

    KaggleDiscovery(api).discover(
        category="gettingStarted",
        search="computer vision",
        group="general",
    )

    assert api.list_arguments is not None
    assert api.list_arguments["category"] == "gettingStarted"
    assert api.list_arguments["search"] == "computer vision"
    assert api.list_arguments["group"] == "general"


def test_passes_requested_sort_order() -> None:
    api = FakeKaggleApi([])

    KaggleDiscovery(api).discover(sort_by="numberOfTeams")

    assert api.list_arguments is not None
    assert api.list_arguments["sort_by"] == "numberOfTeams"


def test_translates_api_failure() -> None:
    api_error = RuntimeError("simulated Kaggle SDK failure")
    api = FakeKaggleApi(error=api_error)

    with pytest.raises(DiscoveryError) as caught:
        KaggleDiscovery(api).discover()

    assert caught.value.__cause__ is api_error


@pytest.mark.parametrize("limit", [0, 201])
def test_rejects_out_of_range_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        KaggleDiscovery(FakeKaggleApi([])).discover(limit=limit)


def example_listed_competition() -> Competition:
    return Competition(
        ref="https://www.kaggle.com/competitions/example-competition",
        title="Example Competition",
        deadline=datetime(2026, 12, 31),
        team_count=10,
        description="Short subtitle.",
        url="https://www.kaggle.com/competitions/example-competition",
    )


def test_load_overview_joins_selected_pages_and_ignores_others() -> None:
    api = FakeKaggleApi(
        pages=[
            SimpleNamespace(name="data-description", content="Do not include."),
            SimpleNamespace(name="rules", content="Legal text."),
            SimpleNamespace(name="Evaluation", content="MRR@25 scoring."),
            SimpleNamespace(name="description", content="Predict SMILES."),
            SimpleNamespace(name="Background", content="How spectra are made."),
            SimpleNamespace(name="Timeline", content="Final deadline in December."),
            SimpleNamespace(name="Prizes", content="$50,000."),
            SimpleNamespace(name="Code Requirements", content="Notebook only."),
        ]
    )

    result = KaggleDiscovery(api).load_overview(example_listed_competition())

    assert api.authenticated is True
    assert api.page_calls == ["example-competition"]
    assert result.description == "Short subtitle."
    assert result.overview is not None
    assert result.overview.startswith("## Description\n\nPredict SMILES.")
    assert "## Background\n\nHow spectra are made." in result.overview
    assert "## Evaluation\n\nMRR@25 scoring." in result.overview
    assert "## Timeline\n\nFinal deadline in December." in result.overview
    assert "## Prizes\n\n$50,000." in result.overview
    assert "## Code Requirements\n\nNotebook only." in result.overview
    assert "Do not include." not in result.overview
    assert "Legal text." not in result.overview


def test_load_overview_is_absent_when_selected_pages_are_missing() -> None:
    api = FakeKaggleApi(
        pages=[SimpleNamespace(name="rules", content="Legal text.")]
    )

    result = KaggleDiscovery(api).load_overview(example_listed_competition())

    assert result.overview is None


def test_load_overview_translates_api_failure() -> None:
    page_error = RuntimeError("simulated page failure")
    api = FakeKaggleApi(page_error=page_error)

    with pytest.raises(DiscoveryError) as caught:
        KaggleDiscovery(api).load_overview(example_listed_competition())

    assert caught.value.__cause__ is page_error


def test_discover_does_not_fetch_overview_pages() -> None:
    api = FakeKaggleApi([minimal_api_competition("only")])

    competitions = KaggleDiscovery(api).discover()

    assert competitions[0].overview is None
    assert api.page_calls == []


def _dated_competition(ref: str, deadline: datetime) -> object:
    item = minimal_api_competition(ref)
    item.deadline = deadline
    item.title = ref
    return item


def test_discover_active_pages_and_keeps_open_competitions() -> None:
    first_page = [
        _dated_competition("closed", datetime(2026, 1, 1)),
        *[_dated_competition(f"old-{index}", datetime(2026, 1, 1)) for index in range(18)],
        _dated_competition("open-one", datetime(2026, 12, 1)),
    ]
    api = FakeKaggleApi(
        responses=[
            SimpleNamespace(competitions=first_page, next_page_token=None),
            SimpleNamespace(
                competitions=[
                    _dated_competition("open-two", datetime(2027, 1, 1)),
                ],
                next_page_token=None,
            ),
        ]
    )

    competitions = KaggleDiscovery(api).discover_active(
        reference_time=datetime(2026, 6, 1),
        limit=20,
    )

    assert [item.ref for item in competitions] == ["open-one", "open-two"]
    assert api.list_calls[0] == {
        "group": "general",
        "sort_by": "earliestDeadline",
        "page_size": 20,
        "page": 1,
    }
    assert api.list_calls[1]["page"] == 2


def test_discover_active_rejects_out_of_range_limit() -> None:
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        KaggleDiscovery(FakeKaggleApi([])).discover_active(
            reference_time=datetime(2026, 6, 1),
            limit=0,
        )
