import time
import json
import threading
from flask import Flask, request, jsonify
from kafka import KafkaProducer

app = Flask(__name__)

# create the producer
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.route('/send_emoji', methods=['POST'])
def send_emoji():
    data = request.json
    if len(data) != 3:
        return jsonify({"status": "failure"}), 400
    for key in ('user_id', 'emoji_type', 'timestamp'):
        if key not in data:
            return jsonify({"status": "failure"}), 400

    send(data)
    print('received emoji', data, 'at', time.time())
    return jsonify({"status": "success"}), 200

def send(emoji):
    producer.send('emoji_topic_unbuffered', emoji)
    producer.flush()
    print('sent emoji', emoji 'at', time.time())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
