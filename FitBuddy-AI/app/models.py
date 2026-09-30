from __future__ import annotations

import json
from typing import Any


def row_to_dict(row) -> dict[str, Any] | None:
    return dict(row) if row else None


def user_from_row(row) -> dict[str, Any] | None:
    data = row_to_dict(row)
    if not data:
        return None
    data["equipment"] = json.loads(data.get("equipment") or "[]")
    return data
