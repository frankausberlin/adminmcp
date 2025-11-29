"""Utility helpers shared within ACP."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def resolve_timestamp() -> str:
    """Return the current UTC timestamp as ISO8601 string."""

    return datetime.now(timezone.utc).isoformat()


def ensure_directory(path: Path) -> Path:
    """Create *path* if it does not exist and return it."""

    path.mkdir(parents=True, exist_ok=True)
    return path
