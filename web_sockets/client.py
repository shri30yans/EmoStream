import asyncio
import websockets

async def listen_to_server():
    """Connect to the WebSocket server and listen for messages."""
    async with websockets.connect('ws://localhost:8765') as websocket:
        while True:
            message = await websocket.recv()
            print(f"Message from server: {message}")

asyncio.run(listen_to_server())