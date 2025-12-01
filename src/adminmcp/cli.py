import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from .logging_config import setup_logging

"""AdminMCP CLI Tool.

This module provides a command-line interface for managing the AdminMCP server,
including starting, stopping, and initializing configuration.
"""

PID_FILE = Path('~/.config/adminmcp/acp_server.pid').expanduser()
PID_FILE = Path('~/.config/adminmcp/acp_server.pid').expanduser()

def is_server_running():
    """Check if the MCP server is currently running.

    This function checks for the existence of a PID file and verifies
    if the process with that PID is still active by sending signal 0.

    Returns:
        bool: True if the server is running, False otherwise.
    """
    if not os.path.exists(PID_FILE):
        return False
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def start_server():
    """Start the MCP server if it's not already running.

    This function checks if the server is already running, and if not,
    launches the server process and saves its PID to a file.
    """
    logger = logging.getLogger(__name__)
    logger.info("Attempting to start server")

    if is_server_running():
        logger.warning("Server is already running")
        print("Server is already running.")
        return

    try:
        process = subprocess.Popen(['python', 'src/adminmcp/server/acp_server.py'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        logger.info(f"Server started with PID {process.pid}")
        print("Server started.")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Failed to start server: {e}")

def stop_server():
    """Stop the MCP server if it's running.

    This function reads the PID from the file, sends a SIGTERM signal
    to the process, and removes the PID file.
    """
    logger = logging.getLogger(__name__)
    logger.info("Attempting to stop server")

    if not os.path.exists(PID_FILE):
        logger.warning("Server is not running (no PID file)")
        print("Server is not running.")
        return

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        logger.info(f"Stopping server with PID {pid}")
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        logger.info("Server stopped successfully")
        print("Server stopped.")
    except OSError as e:
        logger.warning(f"Server was not running: {e}")
        print("Server was not running.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        logger.error(f"Failed to stop server: {e}")
        print(f"Failed to stop server: {e}")

def init_config():
    """Initialize the AdminMCP configuration files.

    This function creates the configuration directory and copies
    the default config file and creates the MCP settings file if they
    don't already exist.
    """
    logger = logging.getLogger(__name__)
    logger.info("Initializing configuration")

    config_dir = Path.home() / '.config' / 'adminmcp'
    config_dir.mkdir(parents=True, exist_ok=True)

    # Copy config.adminmcp.json if not exists
    src_config = Path('config.adminmcp.json')
    dst_config = config_dir / 'config.adminmcp.json'
    if not dst_config.exists():
        shutil.copy2(src_config, dst_config)
        logger.info(f"Copied {src_config} to {dst_config}")
        print(f"Copied {src_config} to {dst_config}")
    else:
        logger.debug(f"{dst_config} already exists")
        print(f"{dst_config} already exists")

    # Create mcp_settings.json if not exists
    settings_file = config_dir / 'mcp_settings.json'
    if not settings_file.exists():
        settings = {"mcpServers": {}}
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Created {settings_file}")
        print(f"Created {settings_file}")
    else:
        logger.debug(f"{settings_file} already exists")
        print(f"{settings_file} already exists")

    logger.info("Configuration initialized successfully")
    print("Configuration initialized.")

# v.0001
def main():
    """Main entry point for the AdminMCP CLI tool.

    This function sets up logging, parses command-line arguments,
    and executes the appropriate command (start/stop server or init config).
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="AdminMCP CLI Tool"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    server_parser = subparsers.add_parser('server', help='Manage the MCP server')
    server_subparsers = server_parser.add_subparsers(dest='action', help='Server actions')

    start_parser = server_subparsers.add_parser('start', help='Start the MCP server')
    stop_parser = server_subparsers.add_parser('stop', help='Stop the MCP server')

    init_parser = subparsers.add_parser('init', help='Initialize configuration')

    args = parser.parse_args()

    if args.command == 'server':
        if args.action == 'start':
            start_server()
        elif args.action == 'stop':
            stop_server()
    elif args.command == 'init':
        init_config()



if __name__ == "__main__":
    main()