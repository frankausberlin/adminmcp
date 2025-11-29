"""Tool management for the ACP server."""

from __future__ import annotations

import asyncio
from asyncio import subprocess as asyncio_subprocess
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Tuple, TYPE_CHECKING

from acp.common.models import ToolCall, ToolInvocationResult

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from acp.server.core import ServerContext

ToolHandler = Callable[[ToolCall, "ServerContext"], Awaitable[ToolInvocationResult]]


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolManager:
    """Registry of tool handlers exposed via MCP-compatible endpoints."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tuple[ToolHandler, ToolDescriptor]] = {}

    def register_tool(self, descriptor: ToolDescriptor, handler: ToolHandler) -> None:
        self._tools[descriptor.name] = (handler, descriptor)

    def register_builtin_tools(self) -> None:
        descriptor = ToolDescriptor(
            name="shell/execute",
            description="Execute a shell command on the host machine with basic policy gating.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command line to execute."},
                    "timeout": {"type": "integer", "default": 7200, "description": "Timeout in seconds."},
                    "dry_run": {"type": "boolean", "default": False, "description": "If true, only evaluate policy."},
                },
                "required": ["command"],
            },
        )
        self.register_tool(descriptor, self._shell_execute)

    def list_tools(self) -> Dict[str, dict]:
        return {
            name: {
                "description": descriptor.description,
                "inputSchema": descriptor.input_schema,
            }
            for name, (_, descriptor) in self._tools.items()
        }

    async def execute(self, call: ToolCall, context: "ServerContext") -> ToolInvocationResult:
        record = self._tools.get(call.name)
        if record is None:
            raise ValueError(f"Unknown tool: {call.name}")
        handler, _ = record
        return await handler(call, context)

    async def _shell_execute(self, call: ToolCall, context: "ServerContext") -> ToolInvocationResult:
        command = str(call.arguments.get("command", ""))
        if not command.strip():
            return ToolInvocationResult(status="DENY", stdout=None, stderr="Missing command to execute.", exit_code=1)
        timeout = int(call.arguments.get("timeout", 7200))
        dry_run = bool(call.arguments.get("dry_run", False))

        policy = context.policy_engine.evaluate(command, mode=call.mode or "logonly", context={"roots": context.roots})
        if policy != "EXECUTE":
            return ToolInvocationResult(status=policy, stdout=None, stderr="Command denied by policy.", exit_code=1)
        if dry_run:
            return ToolInvocationResult(status=policy, stdout="Policy approved", stderr=None, exit_code=0)

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio_subprocess.PIPE,
            stderr=asyncio_subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            return ToolInvocationResult(
                status="TIMEOUT",
                exit_code=124,
                stdout=stdout_bytes.decode("utf-8", errors="ignore") or None,
                stderr="Command timed out.",
            )

        stdout = stdout_bytes.decode("utf-8", errors="ignore") or None
        stderr = stderr_bytes.decode("utf-8", errors="ignore") or None
        return ToolInvocationResult(status="EXECUTE", exit_code=process.returncode, stdout=stdout, stderr=stderr)
