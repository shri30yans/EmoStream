import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

# Example of mocking the WebSocket connection for a single client
async def test_send_emoji_data():
    # Mock the WebSocket connection using AsyncMock
    mock_websocket = AsyncMock()
    
    # Sample emoji data
    emoji_data = {
        "user_id": "user123",
        "emoji_type": "smile",
        "timestamp": 1609459200
    }
    
    # Mock the send method to simulate a WebSocket sending data
    mock_websocket.send = AsyncMock()
    
    # Simulate sending emoji data to the mock WebSocket
    await mock_websocket.send(json.dumps(emoji_data))
    
    # Assert that send was called with the expected emoji data
    mock_websocket.send.assert_called_with(json.dumps(emoji_data))
    print("Test passed for sending emoji data.")

# Example of mocking multiple WebSocket clients
async def test_multiple_clients():
    # Mock two WebSocket connections using AsyncMock
    mock_websocket_1 = AsyncMock()
    mock_websocket_2 = AsyncMock()

    # Sample emoji data
    emoji_data = {
        "user_id": "user123",
        "emoji_type": "smile",
        "timestamp": 1609459200
    }
    
    # Mock send method for both WebSocket clients
    mock_websocket_1.send = AsyncMock()
    mock_websocket_2.send = AsyncMock()

    # Simulate sending emoji data to both clients
    await mock_websocket_1.send(json.dumps(emoji_data))
    await mock_websocket_2.send(json.dumps(emoji_data))

    # Verify both mock clients received the emoji data
    mock_websocket_1.send.assert_called_with(json.dumps(emoji_data))
    mock_websocket_2.send.assert_called_with(json.dumps(emoji_data))

    print("Test passed for multiple clients.")

# Running the mock tests
async def main():
    await test_send_emoji_data()
    await test_multiple_clients()

# Run the tests
if __name__ == "__main__":
    asyncio.run(main())

