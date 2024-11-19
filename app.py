from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
import threading

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/send_emoji', methods=['POST'])
def send_emoji():
    data = request.json
    threading.Thread(target=send_to_kafka, args=(data,)).start()
    return jsonify({"status": "success"}), 200

def send_to_kafka(data):
    producer.send('client_emoji', data)
    producer.flush()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
