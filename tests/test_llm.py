"""Unit tests for the ACP LLM client orchestration layer."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from acp.client.llm import LLMClient
from acp.config import ACPConfig


def _install_openai_stub(monkeypatch: pytest.MonkeyPatch, create_fn):
    """Replace the OpenAI SDK client with a controllable stub."""

    class _DummyClient:
        def __init__(self) -> None:
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create_fn))

    monkeypatch.setattr("acp.client.llm.OpenAI", lambda *args, **kwargs: _DummyClient())


def test_process_request_returns_final_answer_without_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: dict[str, dict] = {}

    def _fake_create(**kwargs):
        recorded["kwargs"] = kwargs
        message = SimpleNamespace(content="final answer", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    _install_openai_stub(monkeypatch, _fake_create)

    api = SimpleNamespace(list_tools=lambda: {}, call_tool=lambda *_args, **_kwargs: None)
    llm = LLMClient(config=ACPConfig(), api=api, api_key="test-key")

    result = llm.process_request("Summarize current status")

    assert result == "final answer"
    assert recorded["kwargs"]["messages"][1]["content"] == "Summarize current status"
    assert "tools" not in recorded["kwargs"]


def test_process_request_runs_tool_calls_until_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    def _fake_create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            tool_call = SimpleNamespace(
                id="call-1",
                type="function",
                function=SimpleNamespace(name="shell__run", arguments='{"command": "ls"}'),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
        else:
            message = SimpleNamespace(content="Done", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    _install_openai_stub(monkeypatch, _fake_create)

    recorded_invocations = []

    class _DummyResult:
        def __init__(self) -> None:
            self.payload = {"status": "ok", "output": "listing"}

        def model_dump(self):
            return self.payload

    def _call_tool(invocation):
        recorded_invocations.append(invocation)
        return _DummyResult()

    api = SimpleNamespace(list_tools=lambda: None, call_tool=_call_tool)
    llm = LLMClient(config=ACPConfig(), api=api, api_key="test-key")

    result = llm.process_request(
        "List files",
        tools={
            "tools": {
                "shell/run": {
                    "description": "Execute shell commands",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                    },
                }
            }
        },
    )

    assert result == "Done"
    assert recorded_invocations[0].name == "shell/run"
    assert recorded_invocations[0].arguments == {"command": "ls"}
    assert calls[0]["tools"][0]["function"]["name"] == "shell__run"


def test_build_tool_specs_derives_aliases_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_openai_stub(monkeypatch, lambda **_kwargs: None)

    llm = LLMClient(config=ACPConfig(), api=SimpleNamespace(list_tools=lambda: {}, call_tool=lambda *_: None), api_key="key")

    specs, alias_map = llm._build_tool_specs(
        {
            "tools": {
                "shell/run": {
                    "description": "Run shell commands",
                    "inputSchema": {"type": "object", "properties": {"cmd": {"type": "string"}}},
                },
                "diagnostics/info": "invalid",
            }
        }
    )

    assert alias_map["shell__run"] == "shell/run"
    assert alias_map["diagnostics__info"] == "diagnostics/info"

    spec_map = {spec.server_name: spec for spec in specs}
    assert "Server tool: shell/run" in spec_map["shell/run"].openai_definition["function"]["description"]
    assert spec_map["shell/run"].openai_definition["function"]["parameters"] == {
        "type": "object",
        "properties": {"cmd": {"type": "string"}},
    }
    assert spec_map["diagnostics/info"].openai_definition["function"]["parameters"] == {"type": "object"}
