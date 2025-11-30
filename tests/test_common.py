"""Tests for shared models and utilities."""

from __future__ import annotations

from datetime import datetime, timezone

from acp.common.models import CommandRequest, LogEntry, LogMetadata, ToolCall
from acp.common.utils import ensure_directory, resolve_timestamp
from acp.config import ACPConfig


def test_resolve_timestamp_returns_utc_isoformat() -> None:
    ts = resolve_timestamp()
    parsed = datetime.fromisoformat(ts)

    assert parsed.tzinfo is not None
    assert parsed.tzinfo.utcoffset(parsed).total_seconds() == 0


def test_ensure_directory_creates_and_is_idempotent(tmp_path) -> None:
    target = tmp_path / "nested" / "dir"

    first_result = ensure_directory(target)
    second_result = ensure_directory(target)

    assert target.exists()
    assert target.is_dir()
    assert first_result == target == second_result


def test_command_request_applies_default_timeout() -> None:
    request = CommandRequest(command="echo test")

    assert request.timeout == 7200


def test_tool_call_defaults_to_logonly_mode() -> None:
    call = ToolCall(name="shell/execute", arguments={})

    assert call.mode == "logonly"


def test_log_entry_optional_streams_are_none_when_empty() -> None:
    entry = LogEntry(
        execution_timestamp_iso="2024-01-01T00:00:00+00:00",
        execution_duration_seconds=0.5,
        command_line="true",
        exit_code=0,
        metadata=LogMetadata(user="tester", parent_pid=1, host="local"),
        stdout=None,
        stderr=None,
    )

    payload = entry.model_dump()

    assert payload["stdout"] is None
    assert payload["stderr"] is None


def test_config_reads_llm_environment(monkeypatch) -> None:
    monkeypatch.setenv("ACP_LLM_KEY", "env-key")
    monkeypatch.setenv("ACP_LLM_BASE_URL", "https://llm.example")
    monkeypatch.setenv("ACP_LLM_MODEL", "gpt-special")

    config = ACPConfig(default_llm_model="unused", default_llm_base_url="https://default")
    settings = config.llm_settings

    assert settings.api_key == "env-key"
    assert settings.base_url == "https://llm.example"
    assert settings.model == "gpt-special"
