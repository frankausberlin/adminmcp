"""Mode persistence for the ACP CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from acp.config import ACPConfig

ACPMode = Literal["logonly", "watch", "dialog"]


@dataclass
class StateManager:
    """Persist and retrieve the current CLI mode."""

    config: ACPConfig

    def _state_file(self) -> Path:
        return self.config.runtime_state_path

    def get_mode(self) -> ACPMode:
        """Return the currently active mode, falling back to logonly."""

        path = self._state_file()
        if not path.exists():
            return "logonly"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("mode", "logonly")
        except json.JSONDecodeError:
            return "logonly"

    def set_mode(self, mode: ACPMode) -> None:
        """Persist a new mode to disk."""

        path = self._state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"mode": mode}), encoding="utf-8")
