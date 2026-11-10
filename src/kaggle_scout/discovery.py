"""Competition discovery through the official Kaggle Python API."""

from dataclasses import replace
from datetime import datetime
from typing import Any

from kaggle_scout.competition import Competition

OVERVIEW_PAGE_NAMES = (
    "Description",
    "Background",
    "Evaluation",
    "Timeline",
    "Prizes",
    "Code Requirements",
)


class DiscoveryError(Exception):
    """Raised when Kaggle competition discovery cannot be completed."""


def _optional_text(value: object) -> str | None:
    """Normalize absent and blank API strings to None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_value(api_competition: object, name: str) -> Any:
    """Read a required API field and fail clearly when it is absent."""
    value = getattr(api_competition, name, None)
    if value is None or value == "":
        raise ValueError(f"Kaggle competition is missing required field: {name}")
    return value


def _tag_names(api_tags: object) -> tuple[str, ...]:
    """Convert Kaggle tag objects into SDK-independent names."""
    if not api_tags:
        return ()

    names: list[str] = []
    for tag in api_tags:
        value = tag if isinstance(tag, str) else getattr(tag, "name", None)
        name = _optional_text(value)
        if name is not None:
            names.append(name)
    return tuple(names)


def map_competition(api_competition: object) -> Competition:
    """Map one Kaggle API object to the application's data contract."""
    deadline = _required_value(api_competition, "deadline")
    if not isinstance(deadline, datetime):
        raise TypeError("Kaggle competition deadline must be a datetime")
    launch_date = getattr(api_competition, "enabled_date", None)

    return Competition(
        ref=str(_required_value(api_competition, "ref")),
        title=str(_required_value(api_competition, "title")),
        description=_optional_text(getattr(api_competition, "description", None)),
        tags=_tag_names(getattr(api_competition, "tags", None)),
        deadline=deadline,
        category=_optional_text(getattr(api_competition, "category", None)),
        reward=_optional_text(getattr(api_competition, "reward", None)),
        evaluation_metric=_optional_text(
            getattr(api_competition, "evaluation_metric", None)
        ),
        date_created=getattr(api_competition, "date_created", None),
        team_count=int(getattr(api_competition, "team_count", 0) or 0),
        url=_optional_text(getattr(api_competition, "url", None)),
        launch_date=launch_date if isinstance(launch_date, datetime) else None,
    )


class KaggleDiscovery:
    """Fetch bounded competition pages and isolate Kaggle-specific objects."""

    PAGE_SIZE = 20
    MAX_LIMIT = 200

    def __init__(self, api: object | None = None) -> None:
        self._api = api

    def discover(
        self,
        *,
        limit: int = 20,
        category: str | None = None,
        search: str | None = None,
        group: str | None = None,
        sort_by: str = "recentlyCreated",
    ) -> list[Competition]:
        """Return at most ``limit`` competitions matching Kaggle constraints."""
        if not 1 <= limit <= self.MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {self.MAX_LIMIT}")

        try:
            api = self._api or self._create_api()
            api.authenticate()
            return self._fetch_pages(
                api,
                limit=limit,
                category=category,
                search=search,
                group=group,
                sort_by=sort_by,
            )
        except DiscoveryError:
            raise
        except (Exception, SystemExit) as error:
            raise DiscoveryError("Kaggle competition discovery failed") from error

    def discover_active(
        self,
        *,
        reference_time: datetime,
        limit: int = 200,
    ) -> list[Competition]:
        """Return open public competitions whose deadline is still ahead."""
        if not 1 <= limit <= self.MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {self.MAX_LIMIT}")

        try:
            api = self._api or self._create_api()
            api.authenticate()
            return self._fetch_active_pages(
                api,
                reference_time=reference_time,
                limit=limit,
            )
        except DiscoveryError:
            raise
        except (Exception, SystemExit) as error:
            raise DiscoveryError("Kaggle competition discovery failed") from error

    def load_overview(self, competition: Competition) -> Competition:
        """Attach Overview page text used for interpretation."""
        try:
            api = self._api or self._create_api()
            api.authenticate()
            pages = api.competition_list_pages(competition_slug(competition))
            return replace(competition, overview=assemble_overview(pages))
        except DiscoveryError:
            raise
        except (Exception, SystemExit) as error:
            raise DiscoveryError("Kaggle competition overview failed") from error

    def _fetch_pages(
        self,
        api: object,
        *,
        limit: int,
        category: str | None,
        search: str | None,
        group: str | None,
        sort_by: str,
    ) -> list[Competition]:
        competitions: list[Competition] = []
        page_token: str | None = None

        while len(competitions) < limit:
            request = {
                "sort_by": sort_by,
                "page_size": min(self.PAGE_SIZE, limit - len(competitions)),
            }
            if category is not None:
                request["category"] = category
            if search is not None:
                request["search"] = search
            if group is not None:
                request["group"] = group
            if page_token is not None:
                request["page_token"] = page_token

            response = api.competitions_list(**request)
            api_competitions = (
                getattr(response, "competitions", None) if response else None
            )
            if not api_competitions:
                break

            remaining = limit - len(competitions)
            competitions.extend(
                map_competition(item) for item in api_competitions[:remaining]
            )

            next_page_token = getattr(response, "next_page_token", None)
            if not next_page_token:
                break
            page_token = next_page_token

        return competitions

    def _fetch_active_pages(
        self,
        api: object,
        *,
        reference_time: datetime,
        limit: int,
    ) -> list[Competition]:
        # Token pagination stops after one page for this endpoint, so active
        # discovery uses page numbers to walk the public general list.
        competitions: list[Competition] = []
        page = 1

        while len(competitions) < limit:
            page_size = min(self.PAGE_SIZE, limit - len(competitions))
            response = api.competitions_list(
                group="general",
                sort_by="earliestDeadline",
                page_size=page_size,
                page=page,
            )
            api_competitions = (
                getattr(response, "competitions", None) if response else None
            )
            if not api_competitions:
                break

            for item in api_competitions:
                mapped = map_competition(item)
                if mapped.deadline > reference_time:
                    competitions.append(mapped)
                    if len(competitions) >= limit:
                        break

            if len(api_competitions) < page_size:
                break
            page += 1

        return competitions

    @staticmethod
    def _create_api() -> object:
        # Lazy import avoids Kaggle's import-time authentication behavior.
        from kaggle.api.kaggle_api_extended import KaggleApi

        return KaggleApi()


def competition_slug(competition: Competition) -> str:
    """Return the Kaggle competition name used by page APIs."""
    source = competition.url or competition.ref
    text = str(source).rstrip("/")
    if "/competitions/" in text:
        return text.split("/competitions/")[-1]
    return text


def assemble_overview(pages: object) -> str | None:
    """Join selected Overview pages in a stable order."""
    contents: dict[str, str] = {}
    for page in pages or ():
        name = _optional_text(getattr(page, "name", None))
        content = _optional_text(getattr(page, "content", None))
        if name is None or content is None:
            continue
        contents[name.casefold()] = content

    sections: list[str] = []
    for name in OVERVIEW_PAGE_NAMES:
        content = contents.get(name.casefold())
        if content is not None:
            sections.append(f"## {name}\n\n{content}")
    return "\n\n".join(sections) if sections else None
