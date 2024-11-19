import asyncio
import websockets
import json
import time
from kafka import KafkaConsumer
import sys

# Get websocket port from environment variable
websocket_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

sockets = []

consumer = KafkaConsumer(
    'emoji_topic_aggregated_to_subscribers',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

last_flush_time = time.time()

async def send_to_all_sockets(message):
    """Send a message to all connected WebSockets."""
    for socket in sockets:
        try:
            await socket.send(message)
        except:
            continue


async def kafka_listener():
    """Listen to Kafka messages and broadcast them to all WebSockets."""
    for message in consumer:
        data = message.value
        print(f"Subscriber received: {data}")
        await send_to_all_sockets(json.dumps(data))

async def main():
    """Start the WebSocket server and Kafka listener."""
    websocket_server = await websockets.serve(websocket_handler, 'localhost', websocket_port)
    print(f"WebSocket server started on ws://localhost:{websocket_port}")
    await kafka_listener()

asyncio.run(main())
