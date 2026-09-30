from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import database_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    goal TEXT NOT NULL,
    experience TEXT NOT NULL,
    days_per_week INTEGER NOT NULL,
    session_minutes INTEGER NOT NULL,
    equipment TEXT NOT NULL DEFAULT '[]',
    diet TEXT NOT NULL,
    limitations TEXT NOT NULL DEFAULT '',
    preferences TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_json TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'demo',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_id INTEGER,
    rating INTEGER NOT NULL,
    energy TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    comments TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE SET NULL
);
"""


def init_db() -> None:
    path = database_path()
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()


@contextmanager
def get_db():
    path = database_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
