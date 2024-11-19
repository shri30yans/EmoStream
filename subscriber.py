from kafka import KafkaConsumer, KafkaProducer
import json
import time
import argparse

print("Subscriber started")
last_flush_time = time.time()

parser = argparse.ArgumentParser()
parser.add_argument('--subscriber_topic', type=str, default='emoji_topic_aggregated_to_subscribers',
                    help='Kafka topic to consume from')

subscriber_topic = parser.parse_args().subscriber_topic

consumer = KafkaConsumer(
    subscriber_topic,
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    data = message.value
    print(f"Subscriber received: {data}")
    
