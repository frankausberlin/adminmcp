"""Tests covering server policy and tool execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from acp.common.models import ToolCall
from acp.config import ACPConfig
from acp.server.core import PolicyEngine, ServerContext
from acp.server.prompts import PromptRegistry
from acp.server.tools import ToolManager


class DummyPolicy:
    def __init__(self, decision: str) -> None:
        self.decision = decision
        self.calls: list[str] = []

    def evaluate(self, command: str, *, mode: str, context) -> str:  # pragma: no cover - trivial
        self.calls.append(command)
        return self.decision


@dataclass
class DummyProcess:
    returncode: int = 0
    stdout_data: bytes = b""
    stderr_data: bytes = b""
    killed: bool = False

    async def communicate(self):
        return self.stdout_data, self.stderr_data

    def kill(self) -> None:
        self.killed = True


def build_context(policy_engine) -> tuple[ServerContext, ToolManager]:
    tool_manager = ToolManager()
    tool_manager.register_builtin_tools()
    context = ServerContext(
        config=ACPConfig(),
        tool_manager=tool_manager,
        prompt_registry=PromptRegistry(),
        policy_engine=policy_engine,
    )
    return context, tool_manager


def test_policy_engine_denies_dangerous_command() -> None:
    engine = PolicyEngine()

    decision = engine.evaluate("rm -rf /tmp", mode="watch", context={})

    assert decision == "DENY"


def test_policy_engine_requests_review_for_watch_keywords() -> None:
    engine = PolicyEngine()

    decision = engine.evaluate("iptables -L", mode="watch", context={})

    assert decision == "ELICIT"


def test_tool_manager_lists_builtin_shell_tool() -> None:
    manager = ToolManager()
    manager.register_builtin_tools()

    tools = manager.list_tools()

    assert "shell/execute" in tools


@pytest.mark.asyncio
async def test_shell_execute_denied_by_policy(monkeypatch) -> None:
    policy = DummyPolicy("DENY")
    context, manager = build_context(policy)

    called = False

    async def fake_create_subprocess_shell(*_, **__):  # pragma: no cover - helper
        nonlocal called
        called = True
        return DummyProcess()

    monkeypatch.setattr("acp.server.tools.asyncio.create_subprocess_shell", fake_create_subprocess_shell)

    call = ToolCall(name="shell/execute", arguments={"command": "ls"}, mode="watch")

    result = await manager.execute(call, context)

    assert result.status == "DENY"
    assert result.exit_code == 1
    assert called is False


@pytest.mark.asyncio
async def test_shell_execute_runs_process_and_returns_output(monkeypatch) -> None:
    policy = DummyPolicy("EXECUTE")
    context, manager = build_context(policy)
    process = DummyProcess(returncode=0, stdout_data=b"done", stderr_data=b"")

    async def fake_create_subprocess_shell(*args, **kwargs):  # pragma: no cover - helper
        return process

    monkeypatch.setattr("acp.server.tools.asyncio.create_subprocess_shell", fake_create_subprocess_shell)

    call = ToolCall(name="shell/execute", arguments={"command": "echo hi"}, mode="dialog")

    result = await manager.execute(call, context)

    assert result.status == "EXECUTE"
    assert result.exit_code == 0
    assert result.stdout == "done"
    assert result.stderr is None


@pytest.mark.asyncio
async def test_shell_execute_reports_timeout(monkeypatch) -> None:
    policy = DummyPolicy("EXECUTE")
    context, manager = build_context(policy)
    process = DummyProcess(returncode=0, stdout_data=b"cached", stderr_data=b"late")

    async def fake_create_subprocess_shell(*args, **kwargs):  # pragma: no cover - helper
        return process

    async def fake_wait_for(awaitable, timeout):  # pragma: no cover - helper
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        raise asyncio.TimeoutError

    monkeypatch.setattr("acp.server.tools.asyncio.create_subprocess_shell", fake_create_subprocess_shell)
    monkeypatch.setattr("acp.server.tools.asyncio.wait_for", fake_wait_for)

    call = ToolCall(name="shell/execute", arguments={"command": "sleep 1", "timeout": 1}, mode="logonly")

    result = await manager.execute(call, context)

    assert result.status == "TIMEOUT"
    assert result.exit_code == 124
    assert process.killed is True
    assert result.stderr == "Command timed out."
