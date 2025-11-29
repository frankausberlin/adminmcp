"""HTTP client wrapper for talking to the ACP server."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from acp.common.models import (
    LogEntry,
    PromptAnalysisRequest,
    PromptAnalysisResponse,
    RootUpdateRequest,
    ServerResponse,
    ToolCall,
    ToolInvocationResult,
)
from acp.config import ACPConfig


class APIClient:
    """Thin wrapper around the REST endpoints exposed by the server."""

    def __init__(self, config: ACPConfig, *, timeout: float = 10.0) -> None:
        self.config = config
        self._timeout = timeout
        self._session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.config.base_url}{path}"

    def send_log(self, entry: LogEntry) -> Optional[ServerResponse]:
        """Send a log entry to the server and return the parsed response if successful."""

        try:
            response = self._session.post(
                self._url("/api/v1/log/submit"),
                json=entry.model_dump(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return ServerResponse(**response.json())
        except requests.RequestException:
            # Network failures should not block the CLI; log submission is best-effort.
            return None

    def update_roots(self, roots: Dict[str, str]) -> ServerResponse:
        """Notify the server about current workspace roots."""

        payload = RootUpdateRequest(roots=roots)
        response = self._session.post(
            self._url("/api/v1/roots/update"),
            json=payload.model_dump(),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return ServerResponse(**response.json())

    def analyze_prompt(self, request: PromptAnalysisRequest) -> PromptAnalysisResponse:
        """Forward a natural-language prompt to the server for analysis."""

        response = self._session.post(
            self._url("/api/v1/prompt/analyze"),
            json=request.model_dump(),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return PromptAnalysisResponse(**response.json())

    def call_tool(self, tool_call: ToolCall) -> ToolInvocationResult:
        """Trigger tool execution on the server and parse the response."""

        requested_timeout = tool_call.arguments.get("timeout")
        network_timeout = (
            max(self._timeout, float(requested_timeout))
            if requested_timeout is not None
            else self._timeout
        )
        response = self._session.post(
            self._url("/api/v1/tools/call"),
            json=tool_call.model_dump(),
            timeout=network_timeout,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        return ToolInvocationResult(**data)

    def list_tools(self) -> Optional[Dict[str, Any]]:
        try:
            response = self._session.get(self._url("/api/v1/tools/list"), timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
