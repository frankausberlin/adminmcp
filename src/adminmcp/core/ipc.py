import asyncio
import json
import logging
import os
import struct
from typing import Any, Callable, Dict, Optional
import uuid

logger = logging.getLogger(__name__)

class IPCError(Exception):
    """Base class for IPC errors."""
    pass

class IPCProtocol:
    """Handles message framing and serialization."""
    
    @staticmethod
    async def send_message(writer: asyncio.StreamWriter, message: Dict[str, Any]) -> None:
        """Send a JSON message with length prefix."""
        try:
            data = json.dumps(message).encode('utf-8')
            length = len(data)
            writer.write(struct.pack('!I', length))
            writer.write(data)
            await writer.drain()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise IPCError(f"Send failed: {e}")

    @staticmethod
    async def receive_message(reader: asyncio.StreamReader) -> Optional[Dict[str, Any]]:
        """Receive a length-prefixed JSON message."""
        try:
            length_data = await reader.readexactly(4)
            length = struct.unpack('!I', length_data)[0]
            data = await reader.readexactly(length)
            return json.loads(data.decode('utf-8'))
        except asyncio.IncompleteReadError:
            return None  # Connection closed
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise IPCError(f"Receive failed: {e}")

class IPCServer:
    """
    Unix Domain Socket Server for IPC.
    """
    def __init__(self, socket_path: str, request_handler: Callable[[Dict[str, Any]], Any]):
        self.socket_path = socket_path
        self.request_handler = request_handler
        self.server: Optional[asyncio.AbstractServer] = None

    async def start(self) -> None:
        """Start the IPC server."""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        self.server = await asyncio.start_unix_server(
            self._handle_client,
            self.socket_path
        )
        logger.info(f"IPC Server listening on {self.socket_path}")

    async def stop(self) -> None:
        """Stop the IPC server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            logger.info("IPC Server stopped")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle incoming client connection."""
        try:
            while True:
                request = await IPCProtocol.receive_message(reader)
                if request is None:
                    break
                
                logger.debug(f"Received request: {request}")
                
                # Process request
                try:
                    if asyncio.iscoroutinefunction(self.request_handler):
                        response = await self.request_handler(request)
                    else:
                        response = self.request_handler(request)
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    response = {"error": str(e), "status": "error"}

                await IPCProtocol.send_message(writer, response)
                
        except IPCError as e:
            logger.error(f"IPC Error in client handler: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

class IPCClient:
    """
    Unix Domain Socket Client for IPC.
    """
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        """Connect to the IPC server."""
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(self.socket_path)
            logger.info(f"Connected to IPC Server at {self.socket_path}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.socket_path}: {e}")
            raise IPCError(f"Connection failed: {e}")

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request and wait for a response."""
        if not self.writer or not self.reader:
            raise IPCError("Not connected")

        # Add ID if not present
        if "id" not in request:
            request["id"] = str(uuid.uuid4())

        await IPCProtocol.send_message(self.writer, request)
        response = await IPCProtocol.receive_message(self.reader)
        
        if response is None:
            raise IPCError("Connection closed by server")
            
        return response

    async def close(self) -> None:
        """Close the connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
            logger.info("IPC Client disconnected")