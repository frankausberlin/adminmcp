import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".config" / "adminmcp"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_pid_file(temp_config_dir):
    """Create a mock PID file path."""
    return temp_config_dir / "acp_server.pid"


@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch, temp_config_dir):
    """Mock configuration paths to use temporary directory."""
    # Mock the PID_FILE path in cli.py
    from adminmcp.cli import PID_FILE
    monkeypatch.setattr('adminmcp.cli.PID_FILE', temp_config_dir / "acp_server.pid")

    # Mock Path.home() to return our temp directory
    mock_home = temp_config_dir.parent.parent
    monkeypatch.setattr('pathlib.Path.home', lambda: mock_home)