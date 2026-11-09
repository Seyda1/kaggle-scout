# 🔎 Kaggle Scout

**Kaggle Scout** is a personalized AI agent that discovers, analyzes, and recommends Kaggle competitions based on a user's skills, interests, experience, and learning goals.

The project is also a hands-on learning journey for understanding how to design, build, evaluate, and improve AI agents.

> **Goal:** Build an agent that doesn't just tell you what competitions exist, but decides which competitions are actually worth your time.

---

## 🎯 Project Goal

Kaggle has hundreds of competitions covering areas such as:

* Tabular Machine Learning

* Computer Vision

* Natural Language Processing

* Time Series

* Recommendation Systems

* Reinforcement Learning

* Generative AI

* Agentic AI

* Simulation

* Research-oriented problems

Finding a competition is easy.

Finding a competition that is **right for you** is much harder.

Kaggle Scout aims to solve this problem by combining:

```text

Competition Discovery

        ↓

Competition Analysis

        ↓

User Profile

        ↓

Skill / Interest Matching

        ↓

Agent Decision

        ↓

Personalized Recommendation

        ↓

User Feedback

        ↓

Memory

        ↓

Improved Recommendations

```

---

# 🤖 What Will the Agent Do?

The final version of Kaggle Scout should be able to:

1. Discover new Kaggle competitions.

2. Collect relevant competition information.

3. Analyze the competition requirements.

4. Identify the skills required.

5. Estimate difficulty and learning value.

6. Compare the competition against the user's profile.

7. Decide whether the competition is worth recommending.

8. Explain *why* it is recommending the competition.

9. Notify the user about interesting competitions.

10. Remember user feedback.

11. Improve future recommendations based on that feedback.

For example:

> ### 🟢 Strong Match — 9/10

>

> **Competition:** Example Computer Vision Competition

>

> **Why I'm recommending it:**

> You already have computer vision experience, but this competition introduces image segmentation, which is a useful skill to add to your current toolkit.

>

> **Skills you already have:**

> Python, ML, Computer Vision

>

> **Skills you'll practice:**

> Image preprocessing, segmentation, model evaluation

>

> **New skill:**

> Segmentation

>

> **Difficulty:** Medium

>

> **Estimated commitment:** 5–8 hours/week

>

> **Learning value:** High

The important part is that the agent should eventually be able to answer:

> **"Why should I care about this competition?"**

rather than simply:

> "Here is a summary of the competition."

---

# 🧠 Why This Is an Agent Project

A simple Kaggle scraper might work like this:

```text

Kaggle

   ↓

Get competitions

   ↓

Summarize

   ↓

Send email

```

That is useful automation, but it doesn't demonstrate much agent behavior.

Kaggle Scout will progressively move toward:

```text

Environment

    ↓

Observe

    ↓

Understand current state

    ↓

Reason about available opportunities

    ↓

Choose what deserves attention

    ↓

Use tools

    ↓

Take action

    ↓

Observe results

    ↓

Update memory

    ↓

Improve future decisions

```

The project will therefore be built incrementally rather than trying to create a complex autonomous system from the beginning.

---

# 🏗️ Project Architecture

The architecture will evolve as the project becomes more sophisticated.

## Initial Architecture

```text

                    ┌───────────────┐

                    │     Kaggle    │

                    └───────┬───────┘

                            │

                            ▼

                  ┌──────────────────┐

                  │ Competition      │

                  │ Discovery        │

                  └────────┬─────────┘

                           │

                           ▼

                  ┌──────────────────┐

                  │ Competition      │

                  │ Analyzer          │

                  └────────┬─────────┘

                           │

                           ▼

                  ┌──────────────────┐

                  │ Recommendation   │

                  │ Engine            │

                  └────────┬─────────┘

                           │

                           ▼

                  ┌──────────────────┐

                  │ Notification     │

                  └──────────────────┘

```

## Future Agent Architecture

```text

                         ┌──────────────────┐

                         │     Kaggle       │

                         │   Environment    │

                         └────────┬─────────┘

                                  │

                                  ▼

                         ┌──────────────────┐

                         │   Discovery      │

                         │      Tool        │

                         └────────┬─────────┘

                                  │

                                  ▼

                    ┌─────────────────────────┐

                    │                         │

                    │       AI AGENT          │

                    │                         │

                    │  Observe → Reason       │

                    │  Plan → Act → Learn     │

                    │                         │

                    └───────────┬─────────────┘

                                │

             ┌──────────────────┼──────────────────┐

             │                  │                  │

             ▼                  ▼                  ▼

      Competition         User Profile        Memory

       Analyzer              Store             Store

             │                  │                  │

             └──────────────────┼──────────────────┘

                                │

                                ▼

                       Recommendation

                           Decision

                                │

                                ▼

                         Notification

                                │

                                ▼

                         User Feedback

                                │

                                └──────────► Memory

```

---

# 🛠️ Technology Stack

The technology stack will intentionally evolve as we learn.

## Core

* Python

* Git / GitHub

* Cursor

* Virtual environment

* Testing framework

## AI

Initially:

* LLM API

* Structured outputs

* Prompt engineering

Later:

* Tool calling

* Agent loops

* Memory

* Planning

* Agent frameworks when justified

Potential future frameworks:

* LangGraph

* LangChain

* Other agent frameworks

We will **not introduce an agent framework just because it is popular**.

We will first understand the underlying concepts and introduce a framework when it solves a real architectural problem.

## Data / Storage

Potential components:

* JSON during early development

* SQLite for structured local storage

* Vector database if semantic memory becomes useful

## Notifications

Potential options:

* Email

* Telegram

* Slack

* Discord

The first implementation will use the simplest option that allows us to test the workflow.

---

# 📁 Planned Repository Structure

The repository will evolve over time.

The target structure is approximately:

```text

kaggle-scout/

│

├── src/

│   ├── discovery/

│   │   └── kaggle_[client.py](http://client.py)

│   │

│   ├── analysis/

│   │   └── competition_[analyzer.py](http://analyzer.py)

│   │

│   ├── recommendation/

│   │   └── [recommender.py](http://recommender.py)

│   │

│   ├── agent/

│   │   ├── [agent.py](http://agent.py)

│   │   ├── [state.py](http://state.py)

│   │   ├── [planner.py](http://planner.py)

│   │   └── [tools.py](http://tools.py)

│   │

│   ├── memory/

│   │   └── [memory.py](http://memory.py)

│   │

│   └── notifications/

│       └── [notifier.py](http://notifier.py)

│

├── tests/

│

├── data/

│   ├── competitions/

│   └── user_profile/

│

├── notebooks/

│

├── .env.example

├── .gitignore

├── requirements.txt

├── [README.md](http://README.md)

└── [main.py](http://main.py)

```

This is the **target architecture**, not the starting architecture.

We should avoid creating unnecessary folders before they are needed.

---

# 🚀 Development Roadmap

The project will be developed in stages.

---

## Phase 0 — Project Setup

### Objective

Create a clean development environment.

### Tasks

* [ ] Create GitHub repository.

* [ ] Create local project.

* [ ] Create Python virtual environment.

* [ ] Configure Cursor.

* [ ] Create `.gitignore`.

* [ ] Create `README.md`.

* [ ] Create initial project structure.

* [ ] Create `.env.example`.

* [ ] Add dependency management.

* [ ] Create initial Git commit.

### Learning Goals

Understand:

* Repository structure

* Environment management

* Configuration

* Secrets

* Git workflow

---

# Phase 1 — Understand the Data Source

### Objective

Before building an agent, understand how we can obtain Kaggle competition information.

We need to determine:

* How competitions can be discovered.

* What information is available.

* How competition details can be retrieved.

* How to identify new competitions.

* How to detect changes.

* How deadlines should be handled.

### Questions We Need to Answer

```text

Where do competitions come from?

What information can we retrieve?

How frequently should we check?

How do we identify a new competition?

How do we store competition information?

How do we avoid processing the same competition repeatedly?

```

### Learning Goals

Learn:

* APIs

* Web data retrieval

* Data normalization

* Persistence

* Idempotency

---

# Phase 2 — Build Competition Discovery

### Objective

Build the first useful component.

The system should be able to:

```text

Discover competitions

        ↓

Extract basic metadata

        ↓

Store competitions

```

Example internal representation:

```json

{

  "title": "Example Competition",

  "url": "...",

  "description": "...",

  "deadline": "...",

  "category": "...",

  "status": "active"

}

```

At this stage there is **no AI agent yet**.

We are building a reliable foundation.

### Learning Goals

Understand:

* Tool interfaces

* External data sources

* Data validation

* Error handling

* Logging

---

# Phase 3 — Competition Analyzer

### Objective

Turn raw competition information into structured knowledge.

### Phase 3A — Deterministic Analysis

Phase 3A derives only objective facts from an existing `Competition`:

* whole days until its deadline, relative to an explicit reference time
* whether a deadline and meaningful evaluation metric are present
* normalized tags with case and duplicate differences removed

Days are calculated by flooring the exact remaining seconds into 24-hour periods.
This means 2.7 days becomes `2`, while a deadline passed by part of a day becomes
`-1`. Supplying the reference time keeps analysis deterministic and testable.

Phase 3A intentionally does **not** infer problem type, domain, required skills,
difficulty, learning value, recommendations, or ranking. Those require
interpretation and belong to Phase 3B.

### Phase 3B — Interpretive Analysis

The LLM should analyze information such as:

```text

Competition description

Rules

Evaluation metric

Dataset

Timeline

Required skills

Constraints

```

and produce structured information.

Example:

```json

{

  "competition_type": "computer_vision",

  "required_skills": [

    "python",

    "deep_learning",

    "image_processing"

  ],

  "difficulty": 4,

  "learning_value": 5,

  "estimated_time": "medium",

  "gpu_required": true

}

```

### Important Principle

The LLM should not return arbitrary prose when the application needs structured information.

We should use structured outputs whenever possible.

### Learning Goals

Understand:

* LLM calls

* Prompt design

* Structured outputs

* Validation

* Hallucination risks

* LLM failure handling

---

# Phase 4 — Build the User Profile

### Objective

Teach the system who it is recommending competitions to.

The profile should contain information such as:

```text

Skills

Interests

Experience

Learning goals

Preferred competition types

Disliked competition types

Time availability

Current learning priorities

```

Example:

```json

{

  "skills": [

    "python",

    "machine_learning",

    "computer_vision",

    "xgboost",

    "catboost",

    "anomaly_detection"

  ],

  "interests": [

    "machine_learning",

    "agentic_ai",

    "ml_engineering"

  ],

  "learning_goals": [

    "agent_development",

    "llm_applications"

  ]

}

```

The profile should evolve as the project evolves.

---

# Phase 5 — Recommendation Engine

### Objective

Determine whether a competition is relevant.

Initially we can use a deterministic scoring system.

For example:

```text

Skill Match        30%

Interest Match     25%

Learning Value     20%

Difficulty Fit     10%

Time Commitment    10%

Novelty              5%

```

This is intentionally not an LLM-only decision.

We want to compare approaches.

### Experiment

Compare:

```text

Rule-based recommendation

            vs

LLM recommendation

            vs

Hybrid recommendation

```

### Learning Goals

Understand:

* Decision systems

* Ranking

* Scoring

* Evaluation

* Hybrid AI systems

---

# Phase 6 — First Real Agent

### Objective

Now we combine everything.

The agent receives:

```text

New competitions

+

User profile

+

Previous recommendations

+

Memory

```

and decides:

```text

Which competitions should I investigate?

Which competitions should I recommend?

What information do I need before deciding?

What tools should I use?

```

The conceptual loop becomes:

```text

OBSERVE

   ↓

REASON

   ↓

PLAN

   ↓

USE TOOL

   ↓

OBSERVE RESULT

   ↓

DECIDE

   ↓

ACT

```

This is the first point where we can genuinely call the system an **agent** rather than just a pipeline.

---

# Phase 7 — Tool Calling

The agent will eventually have access to tools such as:

```text

search_competitions()

get_competition_details()

get_competition_rules()

get_user_profile()

save_memory()

get_previous_feedback()

send_notification()

```

The agent should decide when a tool is needed.

For example:

```text

New competition detected

        ↓

Is the available information enough?

        │

      No

        ↓

Call competition_details()

        ↓

Analyze

        ↓

Is this relevant?

        │

      Yes

        ↓

Generate recommendation

```

### Learning Goals

Understand:

* Tool calling

* Function schemas

* Tool selection

* Tool errors

* Agent loops

---

# Phase 8 — Memory

### Objective

Allow the agent to learn from the user.

Example:

User:

> "Don't recommend competitions that require huge GPU resources."

The system stores:

```text

Preference:

Avoid competitions requiring heavy GPU resources.

```

Later:

```text

New competition

       ↓

Agent checks memory

       ↓

GPU-heavy

       ↓

Lower recommendation score

```

Another example:

User:

> "I'm interested in learning reinforcement learning."

The agent should remember this and adjust future recommendations.

### Learning Goals

Understand:

* Short-term memory

* Long-term memory

* User preferences

* Retrieval

* Memory updates

* Memory quality

---

# Phase 9 — Notifications

### Objective

Automatically deliver recommendations.

Potential workflow:

```text

Scheduled job

      ↓

Discover competitions

      ↓

Agent analyzes them

      ↓

Select top recommendations

      ↓

Generate summaries

      ↓

Send notification

```

Possible channels:

* Email

* Telegram

* Slack

* Discord

Initially, one channel is enough.

---

# Phase 10 — Feedback Loop

This is where the system becomes much more interesting.

After receiving a recommendation, the user can respond:

```text

👍 Interested

👎 Not interested

⏰ Too time-consuming

📚 Already know this

🔥 Want to participate

```

The agent stores this feedback.

Then:

```text

Recommendation

      ↓

User feedback

      ↓

Memory update

      ↓

Future recommendation

      ↓

Better personalization

```

---

# Phase 11 — Evaluation

A recommendation agent needs evaluation.

We should not assume:

> "The LLM says this is a good recommendation, therefore it is good."

We need measurable criteria.

Possible metrics:

### Recommendation Precision

Of the competitions recommended:

```text

How many did the user actually find interesting?

```

### Recommendation Recall

Of the competitions the user would have liked:

```text

How many did the agent discover?

```

### User Feedback

Track:

```text

Interested

Not interested

Participated

Ignored

```

### Learning Improvement

Compare:

```text

Initial recommendations

        vs

Recommendations after feedback

```

The goal is to determine whether the agent actually improves.

---

# Phase 12 — Agent Evaluation

Eventually we should evaluate the **agent itself**.

Questions:

* Does it select the correct tools?

* Does it waste tool calls?

* Does it hallucinate competition information?

* Does it make consistent decisions?

* Does it remember preferences correctly?

* Does it recover from failed tools?

* Does it explain recommendations accurately?

We can create test cases such as:

```text

Given this competition + this user profile:

Should the agent recommend it?

Which tools should it call?

What should its recommendation be?

What evidence should support the recommendation?

```

---

# Phase 13 — Advanced Agent Architecture

Only after understanding the basic architecture should we consider frameworks.

Potential future architecture:

```text

                 ┌───────────────┐

                 │     Agent     │

                 └───────┬───────┘

                         │

              ┌──────────┴──────────┐

              │                     │

              ▼                     ▼

          Planning              Memory

              │                     │

              ▼                     ▼

            Tools              Retrieval

              │                     │

              └──────────┬──────────┘

                         ▼

                    Decision

                         │

                         ▼

                       Action

```

At this stage we may investigate frameworks such as LangGraph if they provide meaningful benefits.

The framework should follow our architecture, not define it.

---

# 🧪 Development Philosophy

This project is primarily a **learning project**.

Therefore:

### We will not:

* Ask Cursor to build the entire project in one prompt.

* Add frameworks without understanding them.

* Treat LLM output as automatically correct.

* Hide all logic behind abstractions.

* Build complicated infrastructure before we need it.

### We will:

* Build incrementally.

* Understand each component.

* Test each component.

* Ask why an architectural decision was made.

* Compare alternative approaches.

* Keep the system observable.

* Experiment with different agent designs.

* Evaluate whether the agent actually improves.

---

# 🖥️ Using Cursor

Cursor will be our primary development environment.

The goal is **not**:

> "Cursor writes the application for us."

The goal is:

> "Cursor is our coding assistant while we learn how to design and build agents."

A typical development cycle will be:

```text

Understand problem

       ↓

Design component

       ↓

Discuss architecture

       ↓

Ask Cursor to implement

       ↓

Read the generated code

       ↓

Test it

       ↓

Debug

       ↓

Improve design

       ↓

Commit

```

When using Cursor Agent, we should give it focused tasks rather than asking it to implement the entire project at once.

---

# 🔐 Configuration & Secrets

Secrets should never be committed to Git.

Use:

```text

.env

```

for local secrets.

Example:

```text

LLM_API_KEY=...

KAGGLE_API_TOKEN=...

```

Commit:

```text

.env.example

```

but never:

```text

.env

```

---

# 🧪 Testing Strategy

Each component should eventually have tests.

Example:

```text

tests/

├── test_[discovery.py](http://discovery.py)

├── test_[analyzer.py](http://analyzer.py)

├── test_[recommender.py](http://recommender.py)

├── test_[memory.py](http://memory.py)

└── test_[agent.py](http://agent.py)

```

We should test both deterministic components and agent behavior.

---

# 📊 Observability

As the agent becomes more complex, we need to understand what it is doing.

We should eventually log:

```text

Timestamp

Competition

Tools called

Tool results

Agent decision

Recommendation score

Reasoning summary

User feedback

```

We should avoid storing sensitive information unnecessarily.

The goal is to be able to answer:

> **"Why did the agent recommend this competition?"**

---

# 🗺️ Current Development Status

## Phase 0 — Setup

* [ ] Repository created

* [ ] Project structure created

* [ ] Python environment configured

* [ ] Cursor configured

* [ ] README created

## Phase 1 — Discovery

* [ ] Identify Kaggle data source

* [ ] Implement competition discovery

* [ ] Store competitions

* [ ] Handle duplicates

* [ ] Handle errors

## Phase 2 — Analysis

* [ ] Extract competition information

* [ ] Build structured competition representation

* [ ] Implement LLM analyzer

* [ ] Validate LLM output

## Phase 3 — Personalization

* [ ] Create user profile

* [ ] Define skill representation

* [ ] Define interest representation

* [ ] Build recommendation scoring

## Phase 4 — Agent

* [ ] Define agent state

* [ ] Define tools

* [ ] Implement agent loop

* [ ] Implement tool calling

* [ ] Implement decision making

## Phase 5 — Memory

* [ ] Store user feedback

* [ ] Retrieve relevant preferences

* [ ] Update preferences

* [ ] Evaluate personalization

## Phase 6 — Notifications

* [ ] Choose notification channel

* [ ] Implement notification tool

* [ ] Schedule agent execution

## Phase 7 — Evaluation

* [ ] Define recommendation metrics

* [ ] Create evaluation dataset

* [ ] Evaluate recommendations

* [ ] Evaluate tool usage

* [ ] Evaluate memory

* [ ] Compare agent versions

## Phase 8 — Advanced Agent

* [ ] Investigate agent frameworks

* [ ] Add planning if necessary

* [ ] Improve memory

* [ ] Improve tool selection

* [ ] Improve evaluation

* [ ] Optimize cost and latency

---

# 🎓 What I Expect to Learn

By completing this project, I want to understand:

### Agent Fundamentals

* What an AI agent actually is

* Agent loops

* State

* Actions

* Observations

* Planning

* Tool use

* Memory

### LLM Engineering

* Prompt design

* Structured outputs

* Function/tool calling

* Context management

* Error handling

* Hallucination mitigation

* LLM evaluation

### Agent Architecture

* Single-agent systems

* Deterministic workflows

* Agentic workflows

* Planning

* Memory

* Tool orchestration

* When to use frameworks

### Production Engineering

* APIs

* Persistence

* Scheduling

* Notifications

* Logging

* Testing

* Configuration

* Secrets

* Deployment

---

# 🚧 Future Ideas

Once the basic system works, Kaggle Scout could evolve into a more capable personal AI research assistant.

Possible future features:

* Track competition deadlines.

* Track competitions the user joined.

* Track competition progress.

* Monitor leaderboard changes.

* Recommend datasets.

* Recommend relevant Kaggle notebooks.

* Recommend learning resources.

* Analyze winning solutions after competitions end.

* Identify skills used by top solutions.

* Recommend competitions specifically to develop missing skills.

* Generate a personalized competition roadmap.

* Compare competitions based on expected learning value.

* Track the user's Kaggle history.

* Learn from completed competitions.

Eventually:

```text

                    Kaggle Scout

                         ↓

             "What should I learn next?"

                         ↓

       ┌─────────────────┼─────────────────┐

       ↓                 ↓                 ↓

 Competitions        Resources        Skills

       ↓                 ↓                 ↓

       └─────────────────┼─────────────────┘

                         ↓

                Personalized Plan

```

---

# 💡 Long-Term Vision

The ultimate goal is not simply to build a Kaggle scraper.

The goal is to build a **personal AI agent that understands what I know, what I am interested in, what I want to learn next, and which opportunities are worth my time.**

Kaggle is the initial environment because it provides a concrete and measurable problem.

The deeper objective is to learn how to build **autonomous, tool-using, stateful, personalized AI systems.**

---

# 📌 Project Principle

> **Build small. Understand deeply. Evaluate continuously. Add complexity only when it solves a real problem.**

This repository is both a software project and a learning laboratory for agent engineering.

---

# 🚀 Getting Started (Phase 0)

## Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

## Install the project

Install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
python -m pytest
```

## Run the application

```bash
python main.py
```

## User profile

Your profile stays on your machine and is not committed.

1. Copy the example file:

```bash
cp data/user_profile.example.json data/user_profile.json
```

On Windows PowerShell:

```powershell
Copy-Item data\user_profile.example.json data\user_profile.json
```

2. Edit `data/user_profile.json` with your skills, interests, experience level, preferred difficulty levels, and learning goals.
3. The app loads that file through `load_user_profile()`. Friends do the same with their own copy.

Do not commit `data/user_profile.json` — it is listed in `.gitignore`.

## Environment variables

Copy `.env.example` to `.env` and fill in values when needed in later phases:

```bash
cp .env.example .env
```

Do not commit `.env` — it is listed in `.gitignore`.

