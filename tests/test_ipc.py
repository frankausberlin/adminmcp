import asyncio
import os
import tempfile
import pytest
from adminmcp.core.ipc import IPCServer, IPCClient, IPCError

@pytest.mark.asyncio
async def test_ipc_connection_and_messaging():
    # Create a temporary socket path
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test_ipc.sock")
        
        # Define a simple request handler
        async def handler(request):
            return {"status": "ok", "echo": request.get("data")}

        # Start Server
        server = IPCServer(socket_path, handler)
        await server.start()
        
        try:
            # Start Client
            client = IPCClient(socket_path)
            await client.connect()
            
            # Test sending a request
            request_data = {"type": "test", "data": "hello"}
            response = await client.send_request(request_data)
            
            assert response["status"] == "ok"
            assert response["echo"] == "hello"
            
            await client.close()
        finally:
            await server.stop()

@pytest.mark.asyncio
async def test_ipc_server_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test_ipc_restart.sock")
        
        async def handler(request):
            return {"status": "ok"}

        server = IPCServer(socket_path, handler)
        await server.start()
        assert os.path.exists(socket_path)
        await server.stop()
        assert not os.path.exists(socket_path)
        
        # Start again
        await server.start()
        assert os.path.exists(socket_path)
        await server.stop()

@pytest.mark.asyncio
async def test_ipc_client_connection_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "non_existent.sock")
        client = IPCClient(socket_path)
        
        with pytest.raises(IPCError):
            await client.connect()