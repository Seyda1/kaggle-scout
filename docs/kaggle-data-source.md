# Kaggle competition data source

This document records the Phase 1A interface investigation, the Phase 1B
authenticated experiment, and the Phase 1C architectural decision. It does not
describe an implemented discovery client.

## Evidence categories

- **OBSERVED FROM KAGGLE** — directly seen in CLI output or in the authenticated
  Python API response.
- **CLIENT-SIDE INFORMATION** — behavior or schema found in the installed
  `kaggle` 2.2.4 / `kagglesdk` 0.1.37 client source. This does not prove that the
  server always populates a field.
- **PROPOSED FOR KAGGLE SCOUT** — an application design decision, not a Kaggle
  guarantee.
- **UNCERTAIN** — not established by the experiments or installed client source.

## Phase 1A: official CLI

### OBSERVED FROM KAGGLE

`kaggle competitions list` requires authentication. Its output is limited to:

```text
ref
deadline
category
reward
teamCount
userHasEntered
userRank
```

The CLI supports table, CSV, and JSON output. JSON projection remains restricted
to the fields above; requesting `title` produced an unknown-field error.

The command-line interface exposes:

- `--group`
- `--category`
- `--sort-by`
- `--search`
- `--page`
- `--page-size`
- `--page-token`

CLI JSON is awkward for automation: when another page exists, a
`Next Page Token = ...` line is printed before the JSON document. An empty result
is printed as `No competitions found`, not `[]`.

### CLIENT-SIDE INFORMATION

The CLI uses the same Python client underneath, but projects each competition
onto a fixed seven-field list before formatting it. Its restricted output is
therefore a CLI presentation decision, not the full server object.

The CLI help and Python defaults are not fully aligned. We should pass discovery
filters and sorting explicitly instead of relying on undocumented or changing
defaults.

## Phase 1B: authenticated Python API experiment

### API used

The experiment authenticated through Kaggle's existing local mechanism and made
one request:

```python
KaggleApi.competitions_list(page_size=20)
```

Authentication succeeded. No credential value was printed or stored in the
repository.

### OBSERVED FROM KAGGLE

The server returned 20 `ApiCompetition` objects. Field population across those
20 objects was:

| Field | Populated |
|---|---:|
| `ref` | 20/20 |
| `title` | 20/20 |
| `description` | 20/20 |
| `tags` | 20/20 |
| `deadline` | 20/20 |
| `category` | 20/20 |
| `reward` | 20/20 |
| `evaluationMetric` | 13/20 |
| `dateCreated` | 20/20 |
| `url` | 20/20 |
| `enabledDate` | 20/20 |
| `teamCount` | 20/20 |
| `kernelCount` | 0/20 |
| `maxTeamSize` | 20/20 |
| `isKernelsSubmissionsOnly` | 8/20 |
| `organizationName` | 20/20 |
| `hostName` | 20/20 |

A sanitized example from the response:

```text
ref: https://www.kaggle.com/competitions/passenger-screening-algorithm-challenge
title: Passenger Screening Algorithm Challenge
description: Improve the accuracy of the Department of Homeland Security's threat recognition algorithms
tags: [image, logloss]
deadline: 2017-12-15 23:59:00
category: Featured
reward: 1,500,000 Usd
evaluationMetric: Log Loss
dateCreated: 2017-05-26 21:51:26.461000
```

These counts establish what this one response contained. They do not guarantee
future population rates, different categories, or every competition record.
In particular, `evaluationMetric` was absent or empty in 7 of 20 records.

### URL finding

`url` was populated in all 20 returned objects. The installed SDK maps a wire
field named `url` directly to `ApiCompetition.url`; the property is a plain
getter/setter and contains no URL-construction logic.

Therefore, for this experiment, **the URL was returned by the Python API and was
not derived by our application**. Kaggle Scout does not need to construct a URL
from `ref`.

### CLIENT-SIDE INFORMATION

`ApiCompetition` declares more fields than the CLI exposes, including `title`,
`url`, `description`, `organizationName`, `category`, `reward`, `tags`,
`deadline`, `kernelCount`, `teamCount`, `enabledDate`, `maxTeamSize`,
`evaluationMetric`, `isKernelsSubmissionsOnly`, `hostName`, and `dateCreated`.

Some of those fields are optional in the client schema. A declared client
attribute is not evidence that the server will populate it. The Phase 1B counts,
not the schema declaration, are the evidence for the fields observed above.

## Architectural options

### Option A: CLI subprocess

- **Metadata richness:** limited to seven fields; excludes the text and tag
  metadata needed for recommendation.
- **Authentication:** handled by Kaggle, but every subprocess still depends on
  locally configured authentication.
- **Pagination/filtering/sorting:** available through CLI arguments.
- **Error handling:** requires interpreting exit codes and human-readable output.
- **Maintainability/parsing:** weakest option. Extra text can surround JSON, and
  the process boundary adds quoting, executable-path, and platform concerns.
- **Dependencies:** no extra Python package beyond the already required `kaggle`,
  but it adds subprocess integration.
- **Automated discovery:** possible, but unnecessarily brittle.
- **Future metadata:** constrained by the CLI's fixed projection.

### Option B: official Python Kaggle API

- **Metadata richness:** the authenticated experiment returned useful metadata
  omitted by the CLI, including title, description, tags, metric, creation date,
  and URL.
- **Authentication:** reuses the official client's local OAuth/token handling.
  Authentication failure must be translated into an application-level error;
  direct `authenticate()` may raise `SystemExit`.
- **Pagination/filtering/sorting:** exposed as typed method parameters and response
  fields.
- **Error handling:** Python exceptions and typed responses are easier to adapt
  than subprocess output, although Kaggle-specific failures still need a small
  boundary.
- **Maintainability/parsing:** no stdout parsing; returns `ApiCompetition`
  instances with typed dates and counts.
- **Dependencies:** uses the official `kaggle` dependency already in
  `pyproject.toml`.
- **Automated discovery:** best fit of the three options.
- **Future metadata:** richer objects and access to other official client methods
  leave room for justified enrichment later.

### Option C: raw SDK or direct API

- **Metadata richness:** potentially equivalent to the Python wrapper because
  the wrapper uses `kagglesdk`.
- **Authentication:** we would assume lower-level authentication and request
  responsibilities that the Python API already handles.
- **Pagination/filtering/sorting:** present in SDK request objects, but requires
  more mapping code.
- **Error handling:** more transport and SDK details would leak into the
  application.
- **Maintainability:** tied more closely to lower-level implementation details.
- **Parsing:** typed SDK objects avoid CLI parsing.
- **Dependencies:** `kagglesdk` is currently transitive; depending on it directly
  would add an explicit low-level coupling.
- **Automated discovery:** viable, but adds complexity without evidence of a
  compensating benefit.
- **Future metadata:** broad access, but the official Python wrapper already
  exposes what Phase 1 currently needs.

## Decision

> **Decision: Use the official Kaggle Python API as the primary competition
> discovery interface.**

This follows directly from the evidence: one Python list request returned the
metadata required for discovery and future matching, while the CLI discarded
that metadata. The raw SDK provides no observed benefit that justifies taking on
lower-level responsibilities.

This decision does **not** mean every `ApiCompetition` field is guaranteed or that
every declared field belongs in our model. The future client should isolate the
third-party API behind a small application boundary so that missing fields,
authentication failures, and client-version changes do not spread through the
project.

## Proposed minimum Competition model

This is a design only; it is not implemented.

| Application field | Evidence from Phase 1B | Internal status | Why include it |
|---|---|---|---|
| `ref` | **OBSERVED**, 20/20 | Required | Kaggle identity used for deduplication. The observed value was a full competition URL, so code must not assume it is only a slug. |
| `title` | **OBSERVED**, 20/20 | Required | Human-readable identity and a primary recommendation signal. Required is our validation rule, not a Kaggle guarantee. |
| `description` | **OBSERVED**, 20/20 | Optional | High-value text for future matching, but optional in the client schema and not guaranteed globally. |
| `tags` | **OBSERVED**, 20/20 | Optional; default empty collection | Structured topic signals. Empty is a valid absence and simpler than `None` for consumers. |
| `deadline` | **OBSERVED**, 20/20 | Required | Determines whether a competition is actionable. |
| `category` | **OBSERVED**, 20/20 | Optional | Coarse competition type and experience-level signal. |
| `reward` | **OBSERVED**, 20/20 | Optional | Useful context, but not central to learning-oriented recommendations and represented as display text. |
| `evaluation_metric` | **OBSERVED**, 13/20 | Optional | Useful problem-type signal; the measured 65% population rate rules out making it required. |
| `date_created` | **OBSERVED**, 20/20 | Optional | Supports incremental discovery and recency, but should not prevent representing a record if absent. |
| `team_count` | **OBSERVED**, 20/20 | Required integer | Useful popularity/competition signal. The client may default a missing value to `0`, so zero must not be interpreted as proven server data. |
| `url` | **OBSERVED**, 20/20 and mapped from the wire field | Optional | Direct navigation. Store the returned value rather than deriving it. |

### Fields deliberately deferred

- `kernel_count`: empty in 20/20, so it supplies no demonstrated value.
- `is_kernels_submissions_only`: populated in 8/20, but no current Phase 2
  requirement needs it.
- `organization_name` and `host_name`: consistently populated, but the first
  discovery use case does not require host-based recommendation.
- `max_team_size`: consistently populated, but team constraints are not yet a
  stated recommendation requirement.
- `enabled_date`: consistently populated and potentially useful for active-state
  calculation, but `date_created` plus `deadline` are enough for the first model.
- `user_has_entered` and `user_rank`: personalized account state, not intrinsic
  competition metadata.

Deferring these fields does not discard the API capability. It keeps the first
model aligned with current requirements; a field can be added when a concrete
filter, recommendation rule, or user question needs it.

## Implemented discovery boundary (Phase 2A–2B)

`KaggleDiscovery` is the production boundary around the official Python client.
Its public operation is:

```text
discover(
    *,
    limit=20,
    category=None,
    search=None,
    group=None,
    sort_by="recentlyCreated",
) -> list[Competition]
```

The adapter authenticates only when `discover()` is called, passes explicit
constraints to Kaggle, follows page tokens, maps SDK objects to the application
`Competition` dataclass, normalizes optional values, and translates failures to
one application-level `DiscoveryError`.

It does not persist, deduplicate, cache, analyze, rank, recommend, retry, or manage
agent state.

## Pagination

### CLIENT-SIDE INFORMATION

The installed method signature is:

```python
competitions_list(
    group=None,
    category=None,
    sort_by=None,
    page=-1,
    search=None,
    page_size=20,
    page_token=None,
)
```

It returns `ApiListCompetitionsResponse | None`. The response exposes:

```text
competitions
next_page_token
```

Both page-number and token pagination exist. The client source describes token
pagination as the newer path. `page_size` defaults to 20; CLI documentation says
the maximum is 200. The CLI wrapper explicitly rejects using `page` and
`page_token` together, although the Python `competitions_list()` method itself
does not contain the same explicit guard.

### OBSERVED FROM KAGGLE

The Phase 1B request used `page_size=20`, returned 20 records, and reported:

```text
next_page_token present: False
```

That one response does not establish that token pagination is unsupported. It
only establishes that this response supplied no usable next token.

### IMPLEMENTED FOR KAGGLE SCOUT

The caller controls pagination through `limit`, meaning “return at most this many
competitions.” The default is 20 and accepted values are 1–200. This makes every
discovery bounded without adding a second page-count control.

Each request asks for at most 20 items and never more than the remaining limit.
The first request omits `page_token`; later requests pass the response's
`next_page_token`. Discovery stops when:

1. the requested limit is reached;
2. Kaggle returns no next-page token; or
3. Kaggle returns an empty page.

If Kaggle returns a partially filled page with a next token, discovery continues.
If it returns fewer total competitions than requested and no next token, the
shorter list is returned normally. A page may be sliced before mapping so the
result never exceeds `limit`.

**UNCERTAIN:** whether the server provides `next_page_token` for other filters or
sort orders, and whether page-number pagination is more reliable for this
endpoint. The implementation deliberately does not fall back to calculated page
numbers.

## Filtering and sorting

### CLIENT-SIDE INFORMATION

The intended Python method accepts:

- `group`
- `category`
- `sort_by`
- `search`
- `page`
- `page_size`
- `page_token`

The installed client validates these values:

```text
group:    general, entered, inClass
category: featured, research, recruitment, gettingStarted, masters, playground
          ("all" is specially mapped by the wrapper)
sort_by:  grouped, prize, earliestDeadline, latestDeadline,
          numberOfTeams, recentlyCreated
search:   free text
```

### OBSERVED FROM KAGGLE

Phase 1B verified only that `page_size=20` was accepted. It did not experimentally
verify each filter or sort behavior.

### IMPLEMENTED FOR KAGGLE SCOUT

`category`, `search`, and `group` are optional and passed through unchanged when
provided. No semantic interpretation or client-side filtering is performed.
`sort_by` is also passed directly to Kaggle and defaults explicitly to
`recentlyCreated`; Kaggle remains responsible for validating and applying it.

**UNCERTAIN:** exact server semantics for default group/category, closed
competitions, sort stability, search matching, and combinations of filters.

## Authentication and error boundary

### OBSERVED FROM KAGGLE

Competition listing requires authentication. Phase 1B succeeded using Kaggle's
existing local authentication mechanism.

### CLIENT-SIDE INFORMATION

The client supports access-token, legacy API-key, and OAuth credential paths.
Calling `KaggleApi.authenticate()` directly may terminate with `SystemExit` on
missing authentication; API requests may also raise client or HTTP exceptions.

### IMPLEMENTED FOR KAGGLE SCOUT

Credentials remain outside source control and are never accepted or logged by
the adapter. The Kaggle package is imported lazily, so importing Kaggle Scout does
not authenticate or access the network. Authentication, API, and mapping failures
are exposed as `DiscoveryError` with the original exception chained as the cause.
Invalid caller limits raise `ValueError` before authentication.

## Remaining uncertainties

- Population rates were measured over one 20-record response, not all Kaggle
  competitions.
- The experiment's result set included an old 2017 competition; the default list
  selection and ordering should not be assumed suitable for ongoing discovery.
- Token-pagination behavior was not demonstrated by the one response.
- Server semantics for filtering, closed competitions, sorting stability, and
  search remain experimentally unverified.
- Rate limits and safe polling frequency remain unknown.
- Findings are specific to `kaggle` 2.2.4 while `pyproject.toml` currently permits
  `kaggle>=1.6`. Dependency-version policy should be decided when the client is
  implemented.

## Next implementation step

Phase 2A implemented the model and one-page path; Phase 2B added bounded token
pagination, upstream filters/sorting, and error translation. Persistence,
deduplication, retries, analysis, recommendation, and agent behavior remain
deliberately outside Discovery.
