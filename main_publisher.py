from kafka import KafkaConsumer, KafkaProducer
import json
import time
import argparse

print("Main Publisher started")
last_flush_time = time.time()

consumer = KafkaConsumer(
    'emoji_topic_aggregated',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for message in consumer:
    data = message.value
    producer.send("emoji_topic_aggregated_to_clusters", data)
    
    current_time = time.time()
    if current_time - last_flush_time >= 0.5: 
        producer.flush()
        last_flush_time = current_time
