# 🔎 Kaggle Scout

**Kaggle Scout** is a personalized AI agent that discovers, analyzes, and recommends Kaggle competitions based on a user's skills, interests, experience, and learning goals.

The project is also a hands-on learning journey for understanding how to design, build, evaluate, and improve AI agents.

> **Goal:** Build an agent that doesn't just tell you what competitions exist, but decides which competitions are actually worth your time.

---

## How to use

Kaggle Scout runs on your own computer. It reads your profile, asks a local model about each active Kaggle competition, and can email you a ranked report. Nothing is hosted for you. Your profile, your Kaggle login, and your Gmail app password stay on your machine.

You need Python, a Kaggle account, and [Ollama](https://ollama.com) with the model `qwen3:14b`. The model is large. Email is sent through your own Gmail account.

### 1. Install

```bash
python -m venv .venv
```

Activate it:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

```bash
pip install -e ".[dev]"
ollama pull qwen3:14b
```

Leave Ollama running while you use Kaggle Scout.

### 2. Kaggle login

Create an API token in your Kaggle account settings and save it as a file named `kaggle.json`.

- **Windows:** `%USERPROFILE%\.kaggle\kaggle.json`
- **macOS / Linux:** `~/.kaggle/kaggle.json`

Do not commit that file, and do not paste the token into the project.

### 3. Your profile

```bash
cp data/user_profile.example.json data/user_profile.json
```

On Windows PowerShell:

```powershell
Copy-Item data\user_profile.example.json data\user_profile.json
```

Edit `data/user_profile.json`: skills, interests, experience level, preferred difficulty, and learning goals. Each person uses their own file. It is not committed.

### 4. Gmail

Turn on 2-Step Verification, then create an app password at <https://myaccount.google.com/apppasswords>. Copy the example env file and fill in your own values:

```bash
cp .env.example .env
```

Set `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`. `REPORT_RECIPIENT` is optional and defaults to your own address. Do not commit `.env`.

### 5. Run it

Print a report:

```bash
python main.py
```

Print it and send the email:

```bash
python main.py --email
```

The first full run takes a few minutes. Later runs skip competitions already emailed, so a normal day is much shorter. `--all` includes competitions you have already received. Only a successful email is remembered.

### What the email contains

The subject is the count of recommended competitions and the date. The body has three groups: **Recommended**, **Maybe**, and **Not recommended**. Inside each group, the newest start date is first. Each competition shows its score, problem type, difficulty, start date, deadline, the four score parts, which of your learning goals matched, which skills you already have, which skills you would still learn, and the Kaggle link. If nothing new is waiting, the mail says so.

### Every day on Windows

The PC must be on and you must be logged in. The time is the PC's local time. From the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1
```

That registers **Kaggle Scout Daily Report** every day at 09:30. Pass `-Time "08:00"` to change the time. If the PC was off at 09:30, the task runs after you next sign in. The log is `logs/daily_report.log`.

### Limits

- Interests affect the score through the problem type, such as classification. The subject, such as finance or sports, is not a separate check yet.
- Experience level is stored and not used in the score.
- The skill list can include skills the competition does not really need.
- The daily task is a Windows Task Scheduler task. On macOS or Linux, run `python main.py --email` yourself.

The build notes are in [docs/project-plan.md](docs/project-plan.md).

## Tests

```bash
python -m pytest
```
