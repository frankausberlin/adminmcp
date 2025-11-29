"""Configuration helpers for ACP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class ACPConfig:
    """Central configuration object shared across client and server."""

    server_host: str = "127.0.0.1"
    server_port: int = 8765
    state_filename: str = "ai_state.json"
    log_dir_name: str = "bash_session_logs"

    @property
    def base_url(self) -> str:
        """Return the base URL for HTTP calls."""

        return f"http://{self.server_host}:{self.server_port}"

    @property
    def runtime_state_path(self) -> Path:
        """Return the resolved path for the CLI runtime state file."""

        runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp"
        return Path(runtime_dir) / self.state_filename

    @property
    def log_dir_path(self) -> Path:
        """Return the directory where the client stores shell logs."""

        temp_dir = os.environ.get("TMPDIR") or os.environ.get("TEMP") or "/tmp"
        return Path(temp_dir) / self.log_dir_name


DEFAULT_CONFIG = ACPConfig()
