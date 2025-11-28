import asyncio
import logging
import os
import pty
import select
import signal
import struct
import termios
import tty
from typing import Any, Dict, List, Optional

from adminmcp.core.ipc import IPCServer

logger = logging.getLogger(__name__)

class ShellAgent:
    """
    Manages a shell process running in a PTY.
    """
    def __init__(self, socket_path: str, shell_cmd: List[str] = ["/bin/bash"]):
        self.socket_path = socket_path
        self.shell_cmd = shell_cmd
        self.master_fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.ipc_server: Optional[IPCServer] = None
        self.running = False

    async def start(self) -> None:
        """Start the shell process and IPC server."""
        self.pid, self.master_fd = pty.fork()
        
        if self.pid == 0:  # Child process
            try:
                # Execute the shell
                os.execvp(self.shell_cmd[0], self.shell_cmd)
            except Exception as e:
                logger.error(f"Failed to exec shell: {e}")
                os._exit(1)
        else:  # Parent process
            logger.info(f"Started shell process with PID {self.pid}")
            self.running = True
            
            # Set master FD to non-blocking
            os.set_blocking(self.master_fd, False)
            
            # Start IPC server
            self.ipc_server = IPCServer(self.socket_path, self.handle_ipc_request)
            await self.ipc_server.start()
            
            # Start output reader task
            asyncio.create_task(self._read_shell_output())

    async def stop(self) -> None:
        """Stop the shell and IPC server."""
        self.running = False
        
        if self.ipc_server:
            await self.ipc_server.stop()
            
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0)
            except ProcessLookupError:
                pass
            logger.info(f"Stopped shell process {self.pid}")
            
        if self.master_fd:
            os.close(self.master_fd)

    async def handle_ipc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming IPC requests."""
        req_type = request.get("type")
        
        if req_type == "execute_command":
            command = request.get("payload", {}).get("command")
            if not command:
                return {"status": "error", "error": "No command provided"}
            
            return await self._execute_command(command)
            
        elif req_type == "resize":
            rows = request.get("payload", {}).get("rows", 24)
            cols = request.get("payload", {}).get("cols", 80)
            self._resize_pty(rows, cols)
            return {"status": "ok"}
            
        else:
            return {"status": "error", "error": f"Unknown request type: {req_type}"}

    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the shell."""
        if not self.master_fd:
            return {"status": "error", "error": "Shell not running"}

        try:
            # Append newline to execute
            if not command.endswith('\n'):
                command += '\n'
                
            os.write(self.master_fd, command.encode('utf-8'))
            
            # In a real implementation, we would need a way to capture output 
            # specifically for this command and detect when it finishes.
            # For this sprint, we just acknowledge the write.
            return {"status": "ok", "message": "Command sent to shell"}
            
        except Exception as e:
            logger.error(f"Failed to write to shell: {e}")
            return {"status": "error", "error": str(e)}

    async def _read_shell_output(self) -> None:
        """Continuously read output from the shell."""
        while self.running and self.master_fd:
            try:
                # Wait for data to be available
                await asyncio.sleep(0.01)
                
                try:
                    data = os.read(self.master_fd, 1024)
                    if not data:
                        break
                    
                    # Log output for now (later we might broadcast via IPC)
                    # logger.debug(f"Shell output: {data.decode('utf-8', errors='replace')}")
                    
                except BlockingIOError:
                    continue
                except OSError:
                    break
                    
            except Exception as e:
                logger.error(f"Error reading shell output: {e}")
                break

    def _resize_pty(self, rows: int, cols: int) -> None:
        """Resize the PTY window."""
        if self.master_fd:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                import fcntl
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except Exception as e:
                logger.error(f"Failed to resize PTY: {e}")

if __name__ == "__main__":
    # Simple test runner
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        agent = ShellAgent("/tmp/adminmcp-test.sock")
        await agent.start()
        
        print("Agent running. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await agent.stop()

    asyncio.run(main())