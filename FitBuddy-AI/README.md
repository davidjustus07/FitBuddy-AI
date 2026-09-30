# FitBuddy AI

FitBuddy AI is a complete local-first fitness planning demo with a responsive web UI, FastAPI backend, SQLite storage, Gemini integration, deterministic demo mode, feedback-based plan updates, coach dashboard, and JSON APIs.

> **Health note:** FitBuddy is an educational software demo, not medical advice. The generated plans are general wellness suggestions. Users should consult a qualified professional for injuries, medical conditions, pregnancy, eating disorders, or other individual health concerns.

## Features

- Responsive user dashboard
- Profile/onboarding form
- AI-generated weekly workout and nutrition guidance
- Gemini integration through the current `google-genai` SDK
- Local demo mode that works without an API key
- SQLite persistence
- Feedback capture after a plan is generated
- Automatic rule-based plan adjustments from feedback
- Coach dashboard with user, plan, and feedback summaries
- JSON REST endpoints
- Health check endpoint
- No Node.js build step required: FastAPI serves the frontend directly

## 1. Requirements

- Python 3.10+
- VS Code
- Optional: Gemini API key for live AI generation

## 2. Install

### Windows PowerShell

```powershell
cd FitBuddy-AI
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
cd FitBuddy-AI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 3. Run in local demo mode

The included `.env.example` defaults to `DEMO_MODE=true`, so no API key is needed.

```bash
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000/ — FitBuddy user app
- http://127.0.0.1:8000/coach — Coach dashboard
- http://127.0.0.1:8000/docs — Swagger API docs
- http://127.0.0.1:8000/health — health check

## 4. Enable Gemini

Create a Gemini API key in Google AI Studio, then edit `.env`:

```env
DEMO_MODE=false
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Restart the server. The backend uses `google-genai` and `client.models.generate_content(...)`. If Gemini is unavailable at runtime, FitBuddy automatically falls back to the local deterministic generator so the app remains usable.

## 5. API overview

### Create/update a profile

`POST /api/users`

```json
{
  "name": "Aisha",
  "age": 21,
  "goal": "strength",
  "experience": "beginner",
  "days_per_week": 4,
  "session_minutes": 45,
  "equipment": ["dumbbells"],
  "diet": "vegetarian",
  "limitations": "none",
  "preferences": "Short workouts"
}
```

### Generate a plan

`POST /api/users/{user_id}/plans/generate`

### Send feedback and update the plan

`POST /api/users/{user_id}/feedback`

```json
{
  "plan_id": 1,
  "rating": 4,
  "energy": "good",
  "difficulty": "just_right",
  "comments": "I enjoyed the sessions but want a little more mobility."
}
```

### List users

`GET /api/users`

### Coach summary

`GET /api/coach/summary`

### Recent feedback

`GET /api/feedback?limit=20`

## 6. Test

With the virtual environment active:

```bash
pytest -q
```

The tests use the local generator and a temporary SQLite database, so they do not require a Gemini key.

## 7. Project structure

```text
FitBuddy-AI/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   ├── main.py
│   └── static/
│       ├── index.html
│       ├── coach.html
│       ├── styles.css
│       ├── app.js
│       └── coach.js
├── data/
│   └── .gitkeep
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 8. Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`

Activate `.venv` and run `pip install -r requirements.txt` again.

### Gemini errors

Confirm `DEMO_MODE=false`, `GEMINI_API_KEY` is present, and the model name is valid for your API account. FitBuddy will return a demo plan if the Gemini request fails.

### Port already in use

Run:

```bash
uvicorn app.main:app --reload --port 8001
```

Then open http://127.0.0.1:8001/.
