import asyncio
import logging
import os
import sys
import tempfile

from adminmcp.core.shell_agent import ShellAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

async def main():
    """
    Runner for the ShellAgent.
    Starts the TUI and IPC server.
    """
    # Determine socket path
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())
    socket_path = os.path.join(runtime_dir, f"adminmcp-{os.getuid()}.sock")
    
    logger.info(f"Starting AdminMCP Agent with socket: {socket_path}")
    
    # Initialize Agent
    agent = ShellAgent(socket_path)
    
    try:
        # Start Agent (this starts TUI and IPC server)
        await agent.start()
        
        # Keep running until interrupted
        while agent.running:
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await agent.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass