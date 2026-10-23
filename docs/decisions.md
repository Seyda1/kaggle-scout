# Kaggle Scout decisions

This file records product and design decisions, with dates and reasons. It is a memory aid, not a changelog of every file.

Dates use the day the decision was made or confirmed in this project. Earlier phases were built before the October 2026 recommendation work.

---

## 2026-09-11 — Use a local Ollama model for interpretation

**Decision:** Interpret competitions with a local Ollama model (`qwen3:14b`) through a thin HTTP client. Keep a provider boundary so tests never call a real model.

**Why:** Analysis needs language understanding that the deterministic analyzer cannot provide. A local model avoids sending competition text to a hosted API. The provider interface keeps unit tests offline.

---

## 2026-09-22 — Store a structured user profile

**Decision:** `UserProfile` holds skills, experience level, interests, preferred difficulty levels, and learning goals. Collections are immutable tuples. Empty collections are allowed.

**Why:** Recommendation needs a stable user side to compare against an interpretation. Validation belongs on the model so bad profiles fail early.

---

## 2026-10-22 — Score with four fixed signals

**Decision:** `RecommendationEngine` scores four signals and weights them:

- skill match: 30%
- difficulty match: 10%
- interest match: 20%
- learning value: 40%

`experience_level` and `learning_goals` are stored on the profile but are not used in scoring.

**Why:** The first scorer should be deterministic and explainable. Learning value was treated as the strongest signal because the project is for choosing competitions to learn from, not to win. Weights stay fixed unless explicitly changed.

---

## 2026-10-22 — Skill score is exact overlap, not meaning

**Decision:** Skill match is:

```text
number of shared skills / number of required skills
```

Both sides are normalized first: trim, lowercase, treat `_` and `-` as spaces, collapse extra spaces. Duplicates count once. If either side is empty, the score is the neutral value `0.5`.

The explanation labels are:

- `>= 0.80`: Strong skill match
- `>= 0.50`: Partial skill match
- otherwise: Limited skill match

**Why:** Exact overlap is easy to check and to explain. Semantic matching (“pandas means data analysis”) would hide why a score moved. The cost is that related words do not match unless they are written the same way.

**How the Enveda 0.60 was produced (2026-10-23 live test):**

Model `skills_required`:

- machine learning
- deep learning
- feature engineering
- data analysis
- python

Profile skills:

- python
- machine learning
- pandas
- scikit-learn
- feature engineering

Shared after normalization: python, machine learning, feature engineering.

`3 / 5 = 0.60` → Partial skill match.

Not counted:

- pandas and scikit-learn: on the profile, but not in `skills_required`
- deep learning and data analysis: required by the model, but not on the profile, and they do not match any profile skill by exact text

This is set intersection. Nothing in the code judged that “data analysis” is close to “pandas”.

---

## 2026-10-22 — Interest score compares only problem type

**Decision (updated 2026-10-23):** Interests are compared with `problem_type` only, as a whole word or phrase. `domain` does not affect interest match. Empty interests or `problem_type="unknown"` score `0.5`. `problem_type="other"` is a mismatch (`0.0`), not unknown.

**Why:** Domain is industry context (healthcare, chemistry). Counting it as an interest made a chemistry competition look aligned with a “healthcare” or “chemistry” interest even when the user meant a technical interest. The later rule was: sector belongs in `domain` only.

---

## 2026-10-22 — Difficulty and learning-value rules

**Decision:**

- Difficulty: `1.0` if the interpreted difficulty is in the user’s preferred list, `0.0` if not, `0.5` if difficulty is unknown or the user stated no preference.
- Learning value: low `0.0`, medium `0.5`, high `1.0`, unknown `0.5`.

**Why:** These are small, readable mappings. They do not invent a scale between beginner and advanced.

---

## 2026-10-22 — Three recommendation states

**Decision:**

- `recommended` if total score `>= 0.70`
- `maybe` if total score `>= 0.50`
- `not_recommended` otherwise

The explanation summary is the label plus a percentage, for example `Maybe (58%)`. Reasons are phrases derived from the already computed scores. The explainer does not rescore.

**Why:** A single number is hard to act on. Three bands give a first “this is for you / maybe / not for you” answer without changing the weights.

---

## 2026-10-23 — Domain is not a required skill

**Decision:** `skills_required` must be technical skills needed to take part (languages, libraries, methods). Industry or subject knowledge (healthcare, automotive, biology, chemistry knowledge) must not appear there. The sector is described only in `domain`.

This is enforced in the Ollama prompt. It is not filtered in code after the model replies.

**Why:** A five-run Enveda test returned skills such as “chemistry knowledge” and “spectroscopy”. Those made the skill score measure domain familiarity, not whether the user could do the technical work.

**Limit:** A prompt rule is not a guarantee. The model can still emit a domain term. The JSON schema only checks that skills are strings.

---

## 2026-10-23 — Do not count domain as an interest match

**Decision:** Same day as the skill rule: drop `domain` from `_score_interests`.

**Why:** A user can be interested in “electric vehicles” without that making every automotive competition a skill or interest hit. Domain is context for reading the problem, not a matching key.

---

## 2026-10-23 — The list API is not the full competition

**Decision:** Keep `discover()` as a listing call. The list field `description` is the short subtitle (89 characters on Enveda). Full Overview text is fetched later with `load_overview()`.

**Why:** `competitions_list` never returns Overview, Data, or Evaluation pages. The analyzer was scoring a card, not the competition write-up. That is why Enveda kept coming back as `problem_type: other` with generic skills.

---

## 2026-10-23 — Send Overview pages, not the Data tab

**Decision:** `Competition.overview` holds joined text from these Kaggle pages only:

- Description
- Background
- Evaluation (this page already contains Matching and Submission File)
- Timeline
- Prizes
- Code Requirements

Do not fetch `data-description`, `rules`, `foundational-rules`, or acknowledgements. `discover()` does not load pages for every listed competition.

**Why:** Overview is enough to understand the task, metric, submission format, dates, prizes, and notebook limits. The Data tab is longer and more technical; it was deferred so the first fetch stays small. Listing 20 competitions should not make 20 extra page calls.

**How the slug is chosen:** The pages API wants the competition name. `ref` can be a full URL, so the code takes the last path segment of `url` or `ref`.

---

## 2026-10-23 — Use a stand-in profile for now

**Decision:** Live tests use a fixed `UserProfile` written in the test script. That is a stand-in, not a real user account. A way for you to enter or edit skills, interests, and preferences will be added later. The model will still not invent the profile.

The stand-in used in the Enveda tests:

- skills: python, machine learning, pandas, scikit-learn, feature engineering
- experience: intermediate
- interests: tabular data, classification, consumer behavior, electric vehicles
- preferred difficulty: beginner, intermediate
- learning goals: improve classification modeling, practice feature engineering

**Why:** Recommendation needs *some* profile to score against. Building a form, saved account, or profile inference would mix a new product surface into the scoring work. The `UserProfile` model is already the place a real profile will go.

---

## Standing constraints (still in force)

These were set at the start of the project and have not been reversed:

- Do not ask for or print API tokens. Use local Kaggle auth if it is already configured.
- Do not create a real `.env` file or commit credentials.
- Tests must not make real network calls.
- Standard library only for application code, plus the already added `kaggle` dependency.
- No LangChain, LangGraph, agents, databases, persistence, notifications, or retry/logging infrastructure unless asked.
- Do not change scoring weights or decision thresholds unless explicitly approved.
- Do not create commits unless asked.

---

## Open points (not decided)

- Whether to remove the example skill list from the prompt. The 2026-10-23 Enveda run still returned python / machine learning / deep learning / feature engineering / data analysis, which matches the prompt examples.
- Whether `problem_type="other"` should be treated as unknown (`0.5`) instead of a mismatch (`0.0`).
- Whether to fetch `data-description` later.
- Whether to add a fixed allowed skill list, aliases (sklearn / scikit-learn), or an optional-skills field.
- Temperature and seed were left unset so runs can still vary.
