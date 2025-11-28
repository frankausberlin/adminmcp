import asyncio
import logging
import os
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from adminmcp.core.ipc import IPCClient
from adminmcp.core.security import SecurityValidator
from adminmcp.tools.system import get_system_info, list_processes

logger = logging.getLogger(__name__)

class AdminMCPServer:
    """
    MCP Server implementation that delegates to ShellAgent via IPC.
    """
    def __init__(self, ipc_path: str):
        self.ipc_path = ipc_path
        self.ipc_client = IPCClient(ipc_path)
        self.security = SecurityValidator()
        self.app = Server("adminmcp")
        
        self._setup_handlers()

    def _setup_handlers(self):
        """Register MCP handlers."""
        
        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="execute_command",
                    description="Execute a shell command in the persistent shell session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Execution mode: 'autonomous' (default) or 'tutor' (requires confirmation).",
                                "enum": ["autonomous", "tutor"],
                                "default": "autonomous"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="system_info",
                    description="Get system information (OS, CPU, Memory).",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ),
                Tool(
                    name="list_processes",
                    description="List running processes.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                )
            ]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent | ImageContent | EmbeddedResource]:
            if name == "execute_command":
                command = arguments.get("command")
                mode = arguments.get("mode", "autonomous")
                
                if not command:
                    raise ValueError("Command is required")
                
                if not self.security.validate_command(command):
                    return [TextContent(type="text", text="Error: Command blocked by security policy.")]

                result = await self._execute_command(command, mode)
                return [TextContent(type="text", text=str(result))]
            
            elif name == "system_info":
                info = get_system_info()
                return [TextContent(type="text", text=str(info))]
            
            elif name == "list_processes":
                procs = list_processes()
                # Limit output to avoid overwhelming the client
                return [TextContent(type="text", text=str(procs[:50]))]

            raise ValueError(f"Unknown tool: {name}")

    async def _execute_command(self, command: str, mode: str = "autonomous") -> Dict[str, Any]:
        """Send command execution request to ShellAgent."""
        try:
            # Ensure connected
            if not self.ipc_client.writer:
                await self.ipc_client.connect()
                
            response = await self.ipc_client.send_request({
                "type": "execute_command",
                "payload": {
                    "command": command,
                    "mode": mode
                }
            })
            return response
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return {"status": "error", "error": str(e)}

    async def run(self):
        """Run the MCP server."""
        # Connect to agent first
        try:
            await self.ipc_client.connect()
        except Exception as e:
            logger.warning(f"Could not connect to agent at startup: {e}")
            # We'll try to connect on demand later

        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )

    async def stop(self):
        """Stop the server and cleanup."""
        await self.ipc_client.close()