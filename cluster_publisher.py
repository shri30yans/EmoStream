from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'aggregated_emoji_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

subscribers = [
    lambda data: print(f"Subscriber 1 received: {data}"),
    lambda data: print(f"Subscriber 2 received: {data}"),
    lambda data: print(f"Subscriber 3 received: {data}")
]

for message in consumer:
    aggregated_data = message.value
    print(f"Cluster Publisher received: {aggregated_data}")
    
    for subscriber in subscribers:
        subscriber(aggregated_data)
