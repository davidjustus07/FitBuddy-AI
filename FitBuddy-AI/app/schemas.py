from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight_loss", "strength", "muscle_gain", "general_fitness", "mobility"]
Experience = Literal["beginner", "intermediate", "advanced"]
Diet = Literal["balanced", "vegetarian", "vegan", "high_protein", "other"]
Energy = Literal["low", "okay", "good", "high"]
Difficulty = Literal["too_easy", "just_right", "too_hard"]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    age: int = Field(ge=13, le=100)
    goal: Goal
    experience: Experience
    days_per_week: int = Field(ge=1, le=7)
    session_minutes: int = Field(ge=10, le=180)
    equipment: list[str] = Field(default_factory=list, max_length=20)
    diet: Diet = "balanced"
    limitations: str = Field(default="", max_length=500)
    preferences: str = Field(default="", max_length=500)

    @field_validator("name", "limitations", "preferences", mode="before")
    @classmethod
    def clean_text(cls, value):
        return " ".join(str(value or "").strip().split())


class FeedbackCreate(BaseModel):
    plan_id: int | None = None
    rating: int = Field(ge=1, le=5)
    energy: Energy
    difficulty: Difficulty
    comments: str = Field(default="", max_length=1000)

    @field_validator("comments", mode="before")
    @classmethod
    def clean_comments(cls, value):
        return " ".join(str(value or "").strip().split())


class PlanResponse(BaseModel):
    id: int
    user_id: int
    version: int
    source: str
    plan: dict
    created_at: str


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int | None
    rating: int
    energy: str
    difficulty: str
    comments: str
    created_at: str
