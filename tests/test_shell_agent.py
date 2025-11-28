import asyncio
import os
import pytest
from unittest.mock import MagicMock, patch
from adminmcp.core.shell_agent import ShellAgent

@pytest.mark.asyncio
async def test_shell_agent_lifecycle():
    with patch('pty.fork') as mock_fork, \
         patch('os.execvp'), \
         patch('os.close'), \
         patch('os.kill'), \
         patch('os.waitpid'), \
         patch('os.set_blocking'), \
         patch('os.read') as mock_read, \
         patch('adminmcp.core.shell_agent.IPCServer') as mock_ipc_cls:
        
        # Setup mocks
        mock_fork.return_value = (123, 7) # pid, master_fd
        
        # Mock IPC Server
        mock_ipc = mock_ipc_cls.return_value
        mock_ipc.start = MagicMock(return_value=asyncio.Future())
        mock_ipc.start.return_value.set_result(None)
        mock_ipc.stop = MagicMock(return_value=asyncio.Future())
        mock_ipc.stop.return_value.set_result(None)
        
        # Mock read to avoid infinite loop or errors
        mock_read.side_effect = BlockingIOError()

        agent = ShellAgent("/tmp/test.sock")
        
        # Start
        await agent.start()
        assert agent.pid == 123
        assert agent.running is True
        
        # Stop
        await agent.stop()
        assert agent.running is False
        mock_ipc.stop.assert_called_once()

@pytest.mark.asyncio
async def test_shell_agent_execution():
    with patch('pty.fork') as mock_fork, \
         patch('os.write') as mock_write, \
         patch('os.set_blocking'), \
         patch('os.read') as mock_read, \
         patch('os.close'), \
         patch('os.kill'), \
         patch('os.waitpid'), \
         patch('adminmcp.core.shell_agent.IPCServer') as mock_ipc_cls:
        
        mock_fork.return_value = (123, 7)
        mock_read.side_effect = BlockingIOError()
        
        # Mock IPC Server
        mock_ipc = mock_ipc_cls.return_value
        mock_ipc.start = MagicMock(return_value=asyncio.Future())
        mock_ipc.start.return_value.set_result(None)
        mock_ipc.stop = MagicMock(return_value=asyncio.Future())
        mock_ipc.stop.return_value.set_result(None)
        
        agent = ShellAgent("/tmp/test.sock")
        await agent.start()
        
        # Execute command
        cmd = "echo test"
        await agent.handle_ipc_request({
            "type": "execute_command", 
            "payload": {"command": cmd}
        })
        
        mock_write.assert_called_with(7, b"echo test\n")
        
        await agent.stop()

@pytest.mark.asyncio
async def test_shell_agent_resize():
    with patch('pty.fork') as mock_fork, \
         patch('os.set_blocking'), \
         patch('os.read') as mock_read, \
         patch('fcntl.ioctl') as mock_ioctl, \
         patch('os.close'), \
         patch('os.kill'), \
         patch('os.waitpid'), \
         patch('adminmcp.core.shell_agent.IPCServer') as mock_ipc_cls:
        
        mock_fork.return_value = (123, 7)
        mock_read.side_effect = BlockingIOError()
        
        # Mock IPC Server
        mock_ipc = mock_ipc_cls.return_value
        mock_ipc.start = MagicMock(return_value=asyncio.Future())
        mock_ipc.start.return_value.set_result(None)
        mock_ipc.stop = MagicMock(return_value=asyncio.Future())
        mock_ipc.stop.return_value.set_result(None)
        
        agent = ShellAgent("/tmp/test.sock")
        await agent.start()
        
        # Resize
        await agent.handle_ipc_request({
            "type": "resize",
            "payload": {"rows": 40, "cols": 100}
        })
        
        assert mock_ioctl.called
        
        await agent.stop()