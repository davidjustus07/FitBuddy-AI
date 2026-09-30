from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any

from .config import DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _goal_label(goal: str) -> str:
    return goal.replace("_", " ").title()


def demo_plan(profile: dict[str, Any], feedback: dict[str, Any] | None = None) -> dict[str, Any]:
    goal = profile["goal"]
    minutes = profile["session_minutes"]
    days = profile["days_per_week"]
    equipment = profile.get("equipment", [])
    feedback = feedback or {}
    difficulty = feedback.get("difficulty")
    adjustment = ""
    intensity = "moderate"
    if difficulty == "too_hard":
        intensity = "light"
        adjustment = "Reduced intensity based on your latest feedback."
    elif difficulty == "too_easy":
        intensity = "challenging"
        adjustment = "Added a small progression based on your latest feedback."
    if feedback.get("energy") == "low":
        intensity = "light"
        adjustment = "Kept sessions lighter because your recent energy was low."

    exercise_bank = {
        "weight_loss": ["Brisk walk", "Bodyweight squat", "Incline push-up", "Reverse lunge", "Dead bug"],
        "strength": ["Goblet squat", "Dumbbell row", "Romanian deadlift", "Push-up", "Plank"],
        "muscle_gain": ["Squat", "Dumbbell press", "Dumbbell row", "Split squat", "Hip hinge"],
        "general_fitness": ["Squat", "Push-up", "Row", "Lunge", "Plank"],
        "mobility": ["Cat-cow", "World's greatest stretch", "90/90 hip flow", "Thoracic rotation", "Hamstring stretch"],
    }
    exercises = exercise_bank.get(goal, exercise_bank["general_fitness"])
    if "dumbbells" not in [e.lower() for e in equipment]:
        exercises = [e for e in exercises if "dumbbell" not in e.lower()] or exercises

    sessions = []
    for i in range(days):
        day = WEEKDAYS[i]
        focus = " + ".join(exercises[:2]) if i % 2 == 0 else " + ".join(exercises[2:4])
        sessions.append({
            "day": day,
            "focus": focus,
            "duration_minutes": minutes,
            "intensity": intensity,
            "warmup_minutes": min(8, max(4, minutes // 8)),
            "exercises": [
                {"name": ex, "sets": 3 if intensity != "light" else 2, "reps": "8-12" if goal != "mobility" else "30-45 sec"}
                for ex in exercises[i % len(exercises): i % len(exercises) + 3]
            ],
        })

    rest_days = [d for d in WEEKDAYS if d not in [s["day"] for s in sessions]]
    nutrition = {
        "principles": [
            "Build meals around vegetables or fruit, a protein source, and a satisfying carbohydrate or healthy fat.",
            "Hydrate regularly and adjust intake to thirst, climate, and activity.",
            "Keep highly processed treats flexible rather than treating foods as forbidden.",
        ],
        "protein_hint": "Include a protein-rich food at each main meal.",
        "diet": profile.get("diet", "balanced"),
    }
    return {
        "title": f"FitBuddy { _goal_label(goal) } Plan",
        "generated_for": profile["name"],
        "week_of": str(date.today()),
        "summary": f"A {days}-day {goal.replace('_', ' ')} routine with {minutes}-minute sessions.",
        "adjustment": adjustment or "This is your starting plan; use your feedback to refine it.",
        "sessions": sessions,
        "rest_days": rest_days,
        "nutrition": nutrition,
        "recovery": [
            "Aim for consistent sleep and take an easier day when recovery is poor.",
            "Stop an exercise if it causes sharp or unusual pain.",
            "Progress gradually rather than changing several training variables at once.",
        ],
        "safety_note": "General wellness guidance only; consult a qualified professional for individual medical or injury-related advice.",
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise ValueError("Gemini did not return a JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Gemini response was not an object")
    return value


def generate_plan(profile: dict[str, Any], feedback: dict[str, Any] | None = None) -> tuple[dict[str, Any], str]:
    if DEMO_MODE or not GEMINI_API_KEY:
        return demo_plan(profile, feedback), "demo"

    prompt = f"""
You are FitBuddy, a conservative general-wellness planning assistant.
Create a practical 7-day fitness and nutrition plan from the user profile below.
Do not diagnose conditions or prescribe treatment. Do not provide unsafe crash diets.
If limitations are present, make the plan cautious and recommend professional guidance where appropriate.
Return ONLY valid JSON. No markdown and no code fences.

Required JSON keys:
 title, generated_for, week_of, summary, adjustment, sessions, rest_days, nutrition, recovery, safety_note

Each sessions item must contain: day, focus, duration_minutes, intensity, warmup_minutes, exercises.
Each exercise must contain: name, sets, reps.

Profile:
{json.dumps(profile, ensure_ascii=False)}

Latest feedback:
{json.dumps(feedback or {}, ensure_ascii=False)}
""".strip()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        plan = _extract_json(response.text or "")
        return plan, "gemini"
    except Exception as exc:
        logger.exception("Gemini generation failed; falling back to demo mode: %s", exc)
        plan = demo_plan(profile, feedback)
        plan["adjustment"] = "Gemini was unavailable, so FitBuddy used its local fallback generator."
        return plan, "demo-fallback"
