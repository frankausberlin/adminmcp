"""Typed models shared between the client and the server."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogMetadata(BaseModel):
    """Metadata describing the environment of a log entry."""

    user: str
    parent_pid: int
    host: str


class LogEntry(BaseModel):
    """Schema describing a shell command execution log."""

    execution_timestamp_iso: str = Field(..., description="ISO8601 timestamp")
    execution_duration_seconds: float
    command_line: str
    exit_code: int
    metadata: LogMetadata
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class RootUpdateRequest(BaseModel):
    """Payload describing root mappings shared with the server."""

    roots: Dict[str, str] = Field(default_factory=dict)


class CommandRequest(BaseModel):
    """Request body for executing a tool or shell command."""

    command: str
    timeout: int = Field(default=7200, description="Timeout in seconds")


class ToolCall(BaseModel):
    """Tool execution description."""

    name: str
    arguments: Dict[str, Any]
    mode: str = Field(default="logonly", description="Client mode triggering the request")


class ToolInvocationResult(BaseModel):
    """Server response after executing a tool."""

    status: str
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class PromptAnalysisRequest(BaseModel):
    """Prompt analysis payload."""

    text: str
    mode: str


class PromptArgument(BaseModel):
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None


class PromptAnalysisResponse(BaseModel):
    """Structured response containing the selected prompt and required arguments."""

    prompt_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    arguments: List[PromptArgument] = Field(default_factory=list)


class ServerResponse(BaseModel):
    """Generic response wrapper with optional payload."""

    message: str
    data: Optional[Dict[str, Any]] = None
