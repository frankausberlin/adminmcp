"""Logging configuration for AdminMCP.

This module provides functions to set up logging for the AdminMCP application,
including file and console handlers with rotation.
"""

import json
import json
import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    """Set up logging configuration for the AdminMCP application.

    This function reads the logging configuration from the config file,
    sets up file and console handlers with rotation, and configures
    the root logger with the specified level.

    The config file should contain 'application' section with 'log_folder'
    and 'logging_level' keys. If the file doesn't exist or is invalid,
    default values are used.
    """
    config_path = Path.home() / '.config' / 'adminmcp' / 'config.adminmcp.json'

    # Default config if file doesn't exist
    config = {
        "application": {
            "log_folder": "~/.local/share/adminmcp/logs",
            "logging_level": "info"
        }
    }

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # Use defaults

    log_folder = Path(config.get('application', {}).get('log_folder', '~/.local/share/adminmcp/logs')).expanduser()
    log_level_str = config.get('application', {}).get('logging_level', 'info').upper()

    # Create log directory if it doesn't exist
    log_folder.mkdir(parents=True, exist_ok=True)

    # Map string levels to logging constants
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = level_map.get(log_level_str, logging.INFO)

    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler with rotation
    log_file = log_folder / 'adminmcp.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # For server, we might not want console output, but for now keep it
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)