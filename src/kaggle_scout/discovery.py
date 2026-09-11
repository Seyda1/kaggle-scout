"""Competition discovery through the official Kaggle Python API."""

from datetime import datetime
from typing import Any

from kaggle_scout.competition import Competition


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

    @staticmethod
    def _create_api() -> object:
        # Lazy import avoids Kaggle's import-time authentication behavior.
        from kaggle.api.kaggle_api_extended import KaggleApi

        return KaggleApi()
