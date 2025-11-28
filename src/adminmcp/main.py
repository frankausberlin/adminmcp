import asyncio
import logging
import os
import sys
import tempfile

from adminmcp.core.shell_agent import ShellAgent
from adminmcp.server import AdminMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

async def main():
    """
    Entry point for AdminMCP.
    Starts both the ShellAgent and the MCP Server.
    """
    # Determine socket path
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())
    socket_path = os.path.join(runtime_dir, f"adminmcp-{os.getuid()}.sock")
    
    logger.info(f"Starting AdminMCP with socket: {socket_path}")
    
    # Initialize Agent
    agent = ShellAgent(socket_path)
    
    # Initialize Server
    server = AdminMCPServer(socket_path)
    
    try:
        # Start Agent
        await agent.start()
        
        # Run Server (this blocks until server stops)
        await server.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        await server.stop()
        await agent.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass