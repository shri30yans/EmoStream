from kafka import KafkaConsumer, KafkaProducer
import json
import time

last_flush_time = time.time()

consumer = KafkaConsumer(
    'emoji_topic_aggregated_to_subscribers',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    data = message.value
    print(f"Subscriber received: {data}")
    
    
