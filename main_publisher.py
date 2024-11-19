from kafka import KafkaConsumer, KafkaProducer
import json
import time

last_flush_time = time.time()

consumer = KafkaConsumer(
    'emoji_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for message in consumer:
    data = message.value
    #print("Recived emoji_topic", data)
    producer.send('emoji_topic', data)
    
    current_time = time.time()
    if current_time - last_flush_time >= 0.5: 
        producer.flush()
        last_flush_time = current_time