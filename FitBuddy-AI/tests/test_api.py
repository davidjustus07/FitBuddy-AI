import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_fitbuddy.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import database_path


def setup_module():
    path = database_path()
    if path.exists():
        path.unlink()


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_create_user_generate_and_feedback():
    with TestClient(app) as client:
        payload = {
            "name": "Test User",
            "age": 22,
            "goal": "strength",
            "experience": "beginner",
            "days_per_week": 3,
            "session_minutes": 30,
            "equipment": ["dumbbells"],
            "diet": "balanced",
            "limitations": "",
            "preferences": "Short sessions",
        }
        user = client.post("/api/users", json=payload)
        assert user.status_code == 201
        user_id = user.json()["id"]

        plan = client.post(f"/api/users/{user_id}/plans/generate")
        assert plan.status_code == 201
        plan_data = plan.json()
        assert plan_data["plan"]["sessions"]

        feedback = client.post(f"/api/users/{user_id}/feedback", json={
            "plan_id": plan_data["id"], "rating": 4, "energy": "good", "difficulty": "too_hard", "comments": "Reduce intensity."
        })
        assert feedback.status_code == 201

        updated = client.post(f"/api/users/{user_id}/plans/generate")
        assert updated.status_code == 201
        assert updated.json()["version"] == 2
        assert "adjustment" in updated.json()["plan"]

        summary = client.get("/api/coach/summary")
        assert summary.status_code == 200
        assert summary.json()["users"] == 1
