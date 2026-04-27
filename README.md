# QA Experiment — Task Manager

A simple Task Management web app used as a test target for exploring AI-assisted QA automation and a human-in-the-loop CI/CD pipeline.

---

## Tech Stack

| Layer | Technology |
|---|---|
| App backend | Python 3.13, Flask, SQLite |
| App frontend | Vanilla JavaScript, HTML/CSS |
| Test automation | pytest, Playwright (UI), requests (API) |
| CI/CD | GitHub Actions |
| AI analysis | Claude API (Haiku) — failure triage in CI |
| Notifications | Telegram Bot |

---

## Repository Structure

```
qa-agent-project/
├── app.py                     # Flask Task Manager app
├── templates/
│   └── index.html             # Frontend UI
├── tests/
│   ├── conftest.py            # Auto-cleanup fixture
│   ├── test_smoke.py
│   ├── test_create_task.py    # TC-001 to TC-005b
│   ├── test_display_filter.py # TC-008 to TC-012
│   ├── test_update_task.py    # TC-013 to TC-018
│   ├── test_delete_task.py    # TC-019 to TC-020
│   └── test_api_validation.py # TC-022 to TC-026
├── analyze_failures.py        # Claude AI failure analysis (CI step)
├── webhook_server.py          # Telegram webhook → GitHub dispatch
├── .github/
│   └── workflows/
│       ├── ci.yml             # Main pipeline: test → analyze → notify
│       └── gate.yml           # Human decision gate
├── pytest.ini
└── requirements.txt
```

---

## Local Setup

**Prerequisites:** Python 3.13+

```bash
# Clone and enter the repo
git clone https://github.com/<your-username>/qa-agent-project.git
cd qa-agent-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

**Run the app:**

```bash
python app.py
# Runs at http://127.0.0.1:5000
```

**Run the tests** (app must be running):

```bash
# All tests
pytest

# Single file
pytest tests/test_create_task.py -v

# Headed browser (visible)
pytest --headed
```

HTML report is generated at `reports/report.html`.

---

## CI/CD Pipeline

```
Push / PR
    │
    ▼
ci.yml
├── Install dependencies
├── Start Flask app
├── Run pytest
├── Claude analyzes failures  ──► Anthropic API
└── Send report to Telegram   ──► Telegram Bot
         │
         ▼
  Human reviews on Telegram
  /approve  or  /reject
         │
         ▼
gate.yml
├── APPROVE → pipeline passes
└── REJECT  → pipeline fails
```

Claude reads the pytest output and returns a BUG / FLAKY verdict per failure, plus an overall APPROVE / REJECT recommendation. The human makes the final call via Telegram before the build result is set.

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### Required for webhook server

| Environment Variable | Description |
|---|---|
| `GITHUB_TOKEN` | Personal access token with `repo` scope |
| `GITHUB_REPO` | e.g. `your-username/qa-agent-project` |

---

## Test Coverage

| File | Test Cases | Area |
|---|---|---|
| test_smoke.py | TC-000 | Page load |
| test_create_task.py | TC-001 to TC-005b | Task creation, input validation |
| test_display_filter.py | TC-008 to TC-012 | Display, filter tabs, stats bar |
| test_update_task.py | TC-013 to TC-018 | Edit, toggle, keyboard shortcuts |
| test_delete_task.py | TC-019 to TC-020 | Delete via UI and API |
| test_api_validation.py | TC-022 to TC-026 | API response format, error handling |

**Note on TC-025:** The backend does not validate the `completed` field — passing `"yes"` returns 500 instead of 400. The test is written against the expected behavior and will fail until the bug is fixed. This is intentional.
