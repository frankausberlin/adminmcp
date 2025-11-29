"""High-level integration smoke tests for the FastAPI server."""

from __future__ import annotations

from fastapi.testclient import TestClient

from acp.common.models import PromptAnalysisRequest
from acp.server.app import create_app


def make_client() -> TestClient:
    return TestClient(create_app())


def test_tool_call_endpoint_allows_dry_run_execution() -> None:
    client = make_client()
    payload = {
        "name": "shell/execute",
        "arguments": {"command": "echo hello", "dry_run": True},
        "mode": "dialog",
    }

    response = client.post("/api/v1/tools/call", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "EXECUTE"


def test_prompt_analysis_endpoint_returns_prompt_metadata() -> None:
    client = make_client()
    request = PromptAnalysisRequest(text="restart the nginx service", mode="dialog")

    response = client.post("/api/v1/prompt/analyze", json=request.model_dump())

    assert response.status_code == 200
    payload = response.json()
    assert payload["prompt_id"] == "/restart_service"
    assert payload["title"]
