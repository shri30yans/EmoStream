from kafka import KafkaConsumer
import json
import asyncio
import websockets

# In-memory set to manage connected WebSocket clients (subscribers)
subscribers = set()

# WebSocket server to handle client subscriptions
async def handle_client(websocket, path):
    subscribers.add(websocket)
        while True:
            await asyncio.sleep(3600)  # Simulate active connection
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            subscribers.remove(websocket)

# Function to send emoji data to all connected WebSocket clients
async def broadcast_emoji_data(emoji_data):
    for websocket in subscribers:
        await websocket.send(json.dumps(emoji_data))

# WebSocket server start
async def start_websocket_server():
    server = await websockets.serve(handle_client, "localhost", 8765)
    await server.wait_closed()

# Start the WebSocket server in a separate thread to not block the Kafka consumer
def start_ws_server():
    asyncio.run(start_websocket_server())

# Start the WebSocket server in the background
import threading
threading.Thread(target=start_ws_server, daemon=True).start()

# Kafka consumer setup
consumer = KafkaConsumer(
    'aggregated_emoji_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    aggregated_data = message.value
    print(f"Cluster Publisher received: {aggregated_data}")
    
    # Call subscribers (here, we're broadcasting to WebSocket clients)
    for subscriber in subscribers:
        subscriber(aggregated_data)
    
    # Broadcast to WebSocket clients
    asyncio.run(broadcast_emoji_data(aggregated_data))

