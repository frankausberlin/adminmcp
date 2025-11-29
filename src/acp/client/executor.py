"""Shell execution and logging utilities for the ACP CLI."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Sequence

from acp.common.models import LogEntry, LogMetadata
from acp.common.utils import ensure_directory, resolve_timestamp
from acp.config import ACPConfig


class CommandExecutor:
    """Execute shell commands, capture output, and persist logs."""

    def __init__(self, config: ACPConfig) -> None:
        self.config = config

    def _log_directory(self) -> Path:
        return ensure_directory(self.config.log_dir_path)

    def _build_log_entry(
        self,
        command: Sequence[str],
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
    ) -> LogEntry:
        metadata = LogMetadata(
            user=os.environ.get("USER") or os.environ.get("USERNAME") or "unknown_user",
            parent_pid=os.getppid(),
            host=os.uname().nodename if hasattr(os, "uname") else "unknown_host",
        )
        return LogEntry(
            execution_timestamp_iso=resolve_timestamp(),
            execution_duration_seconds=round(duration, 4),
            command_line=" ".join(command),
            exit_code=exit_code,
            metadata=metadata,
            stdout=stdout.strip() or None,
            stderr=stderr.strip() or None,
        )

    def _write_log_file(self, entry: LogEntry) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        path = self._log_directory() / f"{timestamp}_shellexecute.json"
        path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")
        return path

    def run(self, command: Sequence[str], timeout: int = 7200) -> LogEntry:
        """Execute *command* and return the structured log entry."""

        start = time.perf_counter()
        try:
            completed = subprocess.run(
                list(command),
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=timeout,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except FileNotFoundError:
            exit_code = 127
            stdout = ""
            stderr = f"Command not found: {command[0]}\n"
        except subprocess.TimeoutExpired:
            exit_code = 124
            stdout = ""
            stderr = f"Command timed out after {timeout} seconds.\n"
        duration = time.perf_counter() - start

        entry = self._build_log_entry(command, exit_code, stdout, stderr, duration)
        self._write_log_file(entry)
        return entry
