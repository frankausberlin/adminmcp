import asyncio
import logging
import os
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from adminmcp.core.ipc import IPCClient

logger = logging.getLogger(__name__)

class AdminMCPServer:
    """
    MCP Server implementation that delegates to ShellAgent via IPC.
    """
    def __init__(self, ipc_path: str):
        self.ipc_path = ipc_path
        self.ipc_client = IPCClient(ipc_path)
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
                            }
                        },
                        "required": ["command"]
                    }
                )
            ]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent | ImageContent | EmbeddedResource]:
            if name == "execute_command":
                command = arguments.get("command")
                if not command:
                    raise ValueError("Command is required")
                
                result = await self._execute_command(command)
                return [TextContent(type="text", text=str(result))]
            
            raise ValueError(f"Unknown tool: {name}")

    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """Send command execution request to ShellAgent."""
        try:
            # Ensure connected
            if not self.ipc_client.writer:
                await self.ipc_client.connect()
                
            response = await self.ipc_client.send_request({
                "type": "execute_command",
                "payload": {
                    "command": command
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