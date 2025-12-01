import json
import os
import pytest
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from adminmcp.cli import (
    is_server_running, start_server, stop_server, init_config, main
)


class TestServerStatus:
    """Test server status checking functionality."""

    @patch('adminmcp.cli.os.path.exists')
    def test_is_server_running_no_pid_file(self, mock_exists):
        """Test when PID file doesn't exist."""
        mock_exists.return_value = False
        assert is_server_running() is False

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.open', new_callable=mock_open, read_data='1234\n')
    @patch('adminmcp.cli.os.kill')
    def test_is_server_running_process_alive(self, mock_kill, mock_file, mock_exists):
        """Test when PID file exists and process is alive."""
        mock_exists.return_value = True
        mock_kill.return_value = None  # Process exists

        assert is_server_running() is True

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.open', new_callable=mock_open, read_data='1234\n')
    @patch('adminmcp.cli.os.kill')
    def test_is_server_running_process_dead(self, mock_kill, mock_file, mock_exists):
        """Test when PID file exists but process is dead."""
        mock_exists.return_value = True
        mock_kill.side_effect = OSError("No such process")

        assert is_server_running() is False


class TestServerStart:
    """Test server starting functionality."""

    @patch('adminmcp.cli.is_server_running')
    @patch('adminmcp.cli.subprocess.Popen')
    @patch('adminmcp.cli.open', new_callable=mock_open)
    @patch('adminmcp.cli.print')
    def test_start_server_success(self, mock_print, mock_file, mock_popen, mock_running):
        """Test successful server start."""
        mock_running.return_value = False
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process

        start_server()

        mock_popen.assert_called_once_with(
            ['python', 'src/adminmcp/server/acp_server.py'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        mock_file.assert_called_once()
        mock_print.assert_called_with("Server started.")

    @patch('adminmcp.cli.is_server_running')
    @patch('adminmcp.cli.print')
    def test_start_server_already_running(self, mock_print, mock_running):
        """Test starting server when already running."""
        mock_running.return_value = True

        start_server()

        mock_print.assert_called_with("Server is already running.")

    @patch('adminmcp.cli.is_server_running')
    @patch('adminmcp.cli.subprocess.Popen')
    @patch('adminmcp.cli.print')
    def test_start_server_failure(self, mock_print, mock_popen, mock_running):
        """Test server start failure."""
        mock_running.return_value = False
        mock_popen.side_effect = Exception("Failed to start")

        start_server()

        mock_print.assert_called_with("Failed to start server: Failed to start")


class TestServerStop:
    """Test server stopping functionality."""

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.print')
    def test_stop_server_no_pid_file(self, mock_print, mock_exists):
        """Test stopping server when no PID file exists."""
        mock_exists.return_value = False

        stop_server()

        mock_print.assert_called_with("Server is not running.")

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.open', new_callable=mock_open, read_data='1234\n')
    @patch('adminmcp.cli.os.kill')
    @patch('adminmcp.cli.os.remove')
    @patch('adminmcp.cli.print')
    def test_stop_server_success(self, mock_print, mock_remove, mock_kill, mock_file, mock_exists):
        """Test successful server stop."""
        mock_exists.return_value = True

        stop_server()

        mock_kill.assert_called_once_with(1234, signal.SIGTERM)
        mock_remove.assert_called_once()
        mock_print.assert_called_with("Server stopped.")

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.open', new_callable=mock_open, read_data='1234\n')
    @patch('adminmcp.cli.os.kill')
    @patch('adminmcp.cli.os.remove')
    @patch('adminmcp.cli.print')
    def test_stop_server_process_not_running(self, mock_print, mock_remove, mock_kill, mock_file, mock_exists):
        """Test stopping server when process is not running."""
        mock_exists.return_value = True
        mock_kill.side_effect = OSError("No such process")

        stop_server()

        mock_kill.assert_called_once_with(1234, signal.SIGTERM)
        mock_remove.assert_called_once()  # Should still remove PID file
        mock_print.assert_called_with("Server was not running.")

    @patch('adminmcp.cli.os.path.exists')
    @patch('adminmcp.cli.open', new_callable=mock_open, read_data='1234\n')
    @patch('adminmcp.cli.os.kill')
    @patch('adminmcp.cli.print')
    def test_stop_server_kill_failure(self, mock_print, mock_kill, mock_file, mock_exists):
        """Test server stop failure."""
        mock_exists.return_value = True
        mock_kill.side_effect = Exception("Kill failed")

        stop_server()

        mock_print.assert_called_with("Failed to stop server: Kill failed")


class TestConfigInit:
    """Test configuration initialization functionality."""

    @patch('adminmcp.cli.Path.home')
    @patch('adminmcp.cli.shutil.copy2')
    @patch('adminmcp.cli.open', new_callable=mock_open)
    @patch('adminmcp.cli.print')
    def test_init_config_success(self, mock_print, mock_file, mock_copy, mock_home):
        """Test successful config initialization."""
        # Use a simpler approach with temporary directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)

            init_config()

            # Should call copy2 and create settings file
            mock_copy.assert_called_once()
            mock_file.assert_called_once()
            assert mock_print.call_count >= 2  # At least config copied and settings created

    @patch('adminmcp.cli.Path.home')
    @patch('adminmcp.cli.shutil.copy2')
    @patch('adminmcp.cli.print')
    def test_init_config_files_exist(self, mock_print, mock_copy, mock_home):
        """Test config init when files already exist."""
        # Mock home directory
        mock_home_dir = MagicMock()
        mock_home.return_value = mock_home_dir

        # Mock config directory
        mock_config_dir = MagicMock()
        mock_home_dir.__truediv__ = MagicMock(return_value=mock_config_dir)
        mock_config_dir.__truediv__ = MagicMock()

        # Mock files that already exist
        mock_dst_config = MagicMock()
        mock_dst_config.exists.return_value = True
        mock_settings_file = MagicMock()
        mock_settings_file.exists.return_value = True

        mock_config_dir.__truediv__.side_effect = [mock_dst_config, mock_settings_file]

        init_config()

        # Should not call copy2 or create files
        mock_copy.assert_not_called()
        mock_print.assert_called()  # Should print that files exist


class TestCLIMain:
    """Test CLI main function."""

    @patch('adminmcp.cli.argparse.ArgumentParser.parse_args')
    @patch('adminmcp.cli.start_server')
    def test_main_server_start(self, mock_start, mock_parse):
        """Test main function with server start command."""
        mock_args = MagicMock()
        mock_args.command = 'server'
        mock_args.action = 'start'
        mock_parse.return_value = mock_args

        main()

        mock_start.assert_called_once()

    @patch('adminmcp.cli.argparse.ArgumentParser.parse_args')
    @patch('adminmcp.cli.stop_server')
    def test_main_server_stop(self, mock_stop, mock_parse):
        """Test main function with server stop command."""
        mock_args = MagicMock()
        mock_args.command = 'server'
        mock_args.action = 'stop'
        mock_parse.return_value = mock_args

        main()

        mock_stop.assert_called_once()

    @patch('adminmcp.cli.argparse.ArgumentParser.parse_args')
    @patch('adminmcp.cli.init_config')
    def test_main_init_config(self, mock_init, mock_parse):
        """Test main function with init config command."""
        mock_args = MagicMock()
        mock_args.command = 'init'
        mock_parse.return_value = mock_args

        main()

        mock_init.assert_called_once()


# Test fixtures
@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".config" / "adminmcp"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_pid_file(temp_config_dir):
    """Create a mock PID file."""
    pid_file = temp_config_dir / "acp_server.pid"
    return pid_file