"""Tests for the ACP client surface (API wrapper + CLI helpers)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest
import requests

from acp.client.api import APIClient
from acp.client.cli import ACPCLI
from acp.common.models import LogEntry, LogMetadata, ToolCall, ToolInvocationResult
from acp.config import ACPConfig


class DummyResponse:
    def __init__(self, payload: Dict[str, Any] | None = None) -> None:
        self._payload = payload or {}

    def raise_for_status(self) -> None:  # pragma: no cover - trivial
        return None

    def json(self) -> Dict[str, Any]:  # pragma: no cover - trivial
        return self._payload


class RecordingSession:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload
        self.called_with: Dict[str, Any] = {}

    def post(self, url: str, json: Dict[str, Any], timeout: float):
        self.called_with = {"url": url, "json": json, "timeout": timeout}
        return DummyResponse(self.payload)


def make_log_entry() -> LogEntry:
    return LogEntry(
        execution_timestamp_iso="2024-01-01T00:00:00+00:00",
        execution_duration_seconds=0.1,
        command_line="echo hi",
        exit_code=0,
        metadata=LogMetadata(user="tester", parent_pid=1, host="local"),
    )


def test_api_client_call_tool_uses_requested_timeout(monkeypatch) -> None:
    client = APIClient(ACPConfig(), timeout=5)
    session = RecordingSession({"status": "EXECUTE", "exit_code": 0})
    client._session = session  # type: ignore[assignment]

    call = ToolCall(name="shell/execute", arguments={"command": "echo", "timeout": 15}, mode="logonly")

    result = client.call_tool(call)

    assert session.called_with["timeout"] == 15  # network timeout matches requested command timeout
    assert result.status == "EXECUTE"


def test_api_client_send_log_swallows_request_errors(monkeypatch) -> None:
    client = APIClient(ACPConfig())

    class FailingSession:
        def post(self, *args, **kwargs):
            raise requests.RequestException("boom")

    client._session = FailingSession()  # type: ignore[assignment]

    response = client.send_log(make_log_entry())

    assert response is None


def test_cli_policy_allows_execution_returns_false_when_server_denies(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    cli.api = SimpleNamespace(  # type: ignore[assignment]
        call_tool=lambda *_: ToolInvocationResult(status="DENY", exit_code=1)
    )

    allowed = cli._policy_allows_execution("rm -rf /", "watch")

    assert allowed is False


def test_cli_policy_allows_execution_fails_open_on_exception(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())

    def _raise(*_args, **_kwargs):
        raise RuntimeError("oops")

    cli.api = SimpleNamespace(call_tool=_raise)  # type: ignore[assignment]

    allowed = cli._policy_allows_execution("echo hi", "watch")

    assert allowed is True


def test_cli_publish_current_roots_calls_api(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    recorded: Dict[str, Dict[str, str]] = {}

    class RecordingAPI:
        def update_roots(self, payload):
            recorded["roots"] = payload
            raise RuntimeError("network down")

    cli.api = RecordingAPI()  # type: ignore[assignment]
    monkeypatch.setattr("acp.client.cli.os.getcwd", lambda: "/tmp/workspace")

    # Should not raise even though the API layer does
    cli._publish_current_roots()

    assert recorded["roots"] == {"cwd": "/tmp/workspace"}


def test_cli_parser_accepts_prompt_text_argument() -> None:
    cli = ACPCLI(ACPConfig())
    parser = cli._build_parser()

    args = parser.parse_args(["--prompt-text", "restart nginx"])

    assert args.prompt_text == "restart nginx"


def test_cli_run_subcommand_delegates_to_handle_command(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    recorded: dict[str, object] = {}

    def _record(command, timeout):
        recorded["command"] = command
        recorded["timeout"] = timeout

    cli._handle_command = _record  # type: ignore[assignment]

    cli.run(["run", "echo", "hi"])

    assert recorded["command"] == ["echo", "hi"]
    assert recorded["timeout"] == 7200


def test_cli_serve_subcommand_invokes_server(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    called = {"serve": False}

    def _mark():
        called["serve"] = True

    cli._start_server = _mark  # type: ignore[assignment]

    cli.run(["serve"])

    assert called["serve"] is True


def test_cli_ask_subcommand_routes_to_handle_ask(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    recorded: dict[str, object] = {}

    def _record(prompt_text: str, *, llm_key, llm_base_url, llm_model):
        recorded["prompt"] = prompt_text
        recorded["key"] = llm_key
        recorded["base_url"] = llm_base_url
        recorded["model"] = llm_model

    cli._handle_ask = _record  # type: ignore[assignment]

    cli.run(["ask", "summarize", "logs"])

    assert recorded["prompt"] == "summarize logs"
    assert recorded["key"] is None
    assert recorded["base_url"] is None
    assert recorded["model"] is None


def test_cli_ask_passes_llm_overrides(monkeypatch) -> None:
    cli = ACPCLI(ACPConfig())
    recorded: dict[str, object] = {}

    def _record(prompt_text: str, *, llm_key, llm_base_url, llm_model):
        recorded["prompt"] = prompt_text
        recorded["key"] = llm_key
        recorded["base_url"] = llm_base_url
        recorded["model"] = llm_model

    cli._handle_ask = _record  # type: ignore[assignment]

    cli.run(
        [
            "--llm-key",
            "override-key",
            "--llm-base-url",
            "https://llm.local",
            "--llm-model",
            "gpt-custom",
            "ask",
            "status",
        ]
    )

    assert recorded["prompt"] == "status"
    assert recorded["key"] == "override-key"
    assert recorded["base_url"] == "https://llm.local"
    assert recorded["model"] == "gpt-custom"
