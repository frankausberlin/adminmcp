import asyncio
import logging
import os
import sys
import tempfile

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
    Runner for the AdminMCPServer.
    Connects to the running ShellAgent via IPC.
    """
    # Determine socket path
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())
    socket_path = os.path.join(runtime_dir, f"adminmcp-{os.getuid()}.sock")
    
    logger.info(f"Starting AdminMCP Server with socket: {socket_path}")
    
    # Initialize Server
    server = AdminMCPServer(socket_path)
    
    try:
        # Run Server (this blocks until server stops)
        # The server will attempt to connect to the agent on startup
        await server.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass