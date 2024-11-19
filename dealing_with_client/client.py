from kafka import KafkaConsumer, KafkaProducer
import json
import threading
import hashlib
from typing import Dict, List, Optional

class EmojiDataConsensusClient:
    def __init__(
        self,
        bootstrap_server: str,
        group_id: str,
        topic: str,
        client_id: Optional[str] = None
    ):
        self.bootstrap_server = bootstrap_server
        self.group_id = group_id
        self.topic = topic
        self.client_id = client_id or f"{group_id}-client"

        # Shared state for consensus
        self.consensus_data: Dict[str, Dict] = {}
        self.consensus_lock = threading.Lock()

        # Initialize consumer
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=[bootstrap_server],
            group_id=group_id,
            client_id=self.client_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

        # Optional Producer for potential consensus messaging
        self.producer = KafkaProducer(
            bootstrap_servers=[bootstrap_server],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def calculate_consensus_hash(self, data: Dict) -> str:
        """Generate a consistent hash for consensus verification."""
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    def process_message(self, message):
        """Process incoming messages and maintain consensus."""
        try:
            emoji_data = json.loads(message.value.decode('utf-8'))
            emoji_hash = self.calculate_consensus_hash(emoji_data)

            with self.consensus_lock:
                emoji_id = emoji_data.get('id')
                if emoji_id not in self.consensus_data:
                    self.consensus_data[emoji_id] = {
                        'data': emoji_data,
                        'consensus_count': 1,
                        'consensus_hash': emoji_hash,
                        'client_ids': {self.client_id}
                    }
                else:
                    existing = self.consensus_data[emoji_id]

                    # Increment consensus if hash matches
                    if existing['consensus_hash'] == emoji_hash:
                        existing['consensus_count'] += 1
                        existing['client_ids'].add(self.client_id)
                    else:
                        print(f"Consensus conflict for emoji {emoji_id}")

        except json.JSONDecodeError:
            print("Invalid JSON message")
        except Exception as e:
            print(f"Message processing error: {e}")

    def consume(self):
        """Continuously consume messages from the topic."""
        try:
            for message in self.consumer:
                self.process_message(message)

        except Exception as e:
            print(f"Consumer error: {e}")
        finally:
            self.consumer.close()

    def get_consensus_data(self) -> Dict:
        """Retrieve current consensus data."""
        with self.consensus_lock:
            return dict(self.consensus_data)

def create_emoji_consensus_clients(
    bootstrap_server: str,
    topic: str,
    num_clients: int = 3
) -> List[EmojiDataConsensusClient]:
    """Create multiple load-balanced consensus clients."""
    clients = []
    for i in range(num_clients):
        group_id = f'emoji-consensus-group'  # Single group for load balancing
        client = EmojiDataConsensusClient(
            bootstrap_server,
            group_id,
            topic,
            client_id=f'emoji-client-{i}'
        )
        clients.append(client)

    # Start each client in a separate thread
    threads = [
        threading.Thread(target=client.consume, daemon=True)
        for client in clients
    ]

    for thread in threads:
        thread.start()

    return clients

# Example Usage
def main():
    bootstrap_server = 'localhost:9092'
    topic = 'aggregated_emoji_data'

    clients = create_emoji_consensus_clients(
        bootstrap_server,
        topic
    )

    # Keep main thread running
    import time
    while True:
        time.sleep(1)
        for client in clients:
            print(f"Client {client.client_id} Consensus Data:")
            print(client.get_consensus_data())

if __name__ == '__main__':
    main()
