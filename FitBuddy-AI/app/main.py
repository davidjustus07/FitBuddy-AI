from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL
from .database import get_db, init_db
from .models import user_from_row
from .schemas import FeedbackCreate, UserCreate
from .services import generate_plan

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="FitBuddy AI API", version="1.0.0", description="AI-assisted wellness planning demo", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/coach", include_in_schema=False)
def coach():
    return FileResponse(STATIC_DIR / "coach.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "demo_mode": DEMO_MODE,
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL,
    }


def _get_user(user_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    user = user_from_row(row)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users", status_code=201)
def create_user(payload: UserCreate):
    data = payload.model_dump()
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE lower(name)=lower(?) ORDER BY id DESC LIMIT 1", (data["name"],)).fetchone()
        if existing:
            user_id = existing["id"]
            db.execute(
                """UPDATE users SET age=?, goal=?, experience=?, days_per_week=?, session_minutes=?, equipment=?, diet=?, limitations=?, preferences=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (data["age"], data["goal"], data["experience"], data["days_per_week"], data["session_minutes"], json.dumps(data["equipment"]), data["diet"], data["limitations"], data["preferences"], user_id),
            )
        else:
            cursor = db.execute(
                """INSERT INTO users (name, age, goal, experience, days_per_week, session_minutes, equipment, diet, limitations, preferences) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["name"], data["age"], data["goal"], data["experience"], data["days_per_week"], data["session_minutes"], json.dumps(data["equipment"]), data["diet"], data["limitations"], data["preferences"]),
            )
            user_id = cursor.lastrowid
    return _get_user(user_id)


@app.get("/api/users")
def list_users():
    with get_db() as db:
        rows = db.execute("SELECT * FROM users ORDER BY updated_at DESC, id DESC").fetchall()
    return [user_from_row(row) for row in rows]


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return _get_user(user_id)


@app.get("/api/users/{user_id}/plans")
def list_plans(user_id: int):
    _get_user(user_id)
    with get_db() as db:
        rows = db.execute("SELECT * FROM plans WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    return [
        {
            "id": row["id"], "user_id": row["user_id"], "version": row["version"],
            "source": row["source"], "plan": json.loads(row["plan_json"]), "created_at": row["created_at"]
        }
        for row in rows
    ]


@app.post("/api/users/{user_id}/plans/generate", status_code=201)
def create_plan(user_id: int):
    user = _get_user(user_id)
    with get_db() as db:
        latest_feedback = db.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        latest_plan = db.execute("SELECT COALESCE(MAX(version),0) AS version FROM plans WHERE user_id=?", (user_id,)).fetchone()
    feedback = dict(latest_feedback) if latest_feedback else None
    plan, source = generate_plan(user, feedback)
    version = int(latest_plan["version"] or 0) + 1
    with get_db() as db:
        cursor = db.execute("INSERT INTO plans (user_id, plan_json, source, version) VALUES (?, ?, ?, ?)", (user_id, json.dumps(plan), source, version))
        plan_id = cursor.lastrowid
        row = db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
    return {"id": row["id"], "user_id": user_id, "version": row["version"], "source": row["source"], "plan": json.loads(row["plan_json"]), "created_at": row["created_at"]}


@app.get("/api/users/{user_id}/feedback")
def list_user_feedback(user_id: int):
    _get_user(user_id)
    with get_db() as db:
        rows = db.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/users/{user_id}/feedback", status_code=201)
def create_feedback(user_id: int, payload: FeedbackCreate):
    _get_user(user_id)
    data = payload.model_dump()
    with get_db() as db:
        if data["plan_id"]:
            plan = db.execute("SELECT id FROM plans WHERE id=? AND user_id=?", (data["plan_id"], user_id)).fetchone()
            if not plan:
                raise HTTPException(status_code=400, detail="plan_id does not belong to this user")
        cursor = db.execute(
            "INSERT INTO feedback (user_id, plan_id, rating, energy, difficulty, comments) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, data["plan_id"], data["rating"], data["energy"], data["difficulty"], data["comments"]),
        )
        feedback_id = cursor.lastrowid
        row = db.execute("SELECT * FROM feedback WHERE id=?", (feedback_id,)).fetchone()
    return {"feedback": dict(row), "message": "Feedback saved. Generate a new plan to apply the update."}


@app.get("/api/feedback")
def list_feedback(limit: int = Query(default=20, ge=1, le=100)):
    with get_db() as db:
        rows = db.execute(
            """SELECT f.*, u.name AS user_name FROM feedback f JOIN users u ON u.id=f.user_id ORDER BY f.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/coach/summary")
def coach_summary():
    with get_db() as db:
        users = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        plans = db.execute("SELECT COUNT(*) AS c FROM plans").fetchone()["c"]
        feedback = db.execute("SELECT COUNT(*) AS c FROM feedback").fetchone()["c"]
        avg = db.execute("SELECT AVG(rating) AS avg FROM feedback").fetchone()["avg"]
        source_rows = db.execute("SELECT source, COUNT(*) AS count FROM plans GROUP BY source").fetchall()
    return {
        "users": users,
        "plans": plans,
        "feedback": feedback,
        "average_rating": round(float(avg), 2) if avg is not None else None,
        "plan_sources": {row["source"]: row["count"] for row in source_rows},
    }
