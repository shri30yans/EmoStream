from kafka import KafkaConsumer, KafkaProducer
import json
import time
import argparse

print("Cluster Publisher started")


parser = argparse.ArgumentParser()
parser.add_argument('--publisher_topic', type=str, default='emoji_topic_aggregated_to_subscribers',
                    help='Kafka topic to produce to')

publisher_topic = parser.parse_args().publisher_topic

last_flush_time = time.time()

consumer = KafkaConsumer(
    'emoji_topic_aggregated_to_clusters',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for message in consumer:
    data = message.value
    producer.send(publisher_topic, data)
    producer.flush()
