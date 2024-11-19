import time
import json
import queue
import threading
from flask import Flask, request, jsonify
from kafka import KafkaProducer

app = Flask(__name__)

emoji_queue = queue.Queue()

@app.route('/send_emoji', methods=['POST'])
def send_emoji():
    data = request.json
    if len(data) != 3:
        return jsonify({"status": "failure"}), 400
    for key in ('user_id', 'emoji_type', 'timestamp'):
        if key not in data:
            return jsonify({"status": "failure"}), 400

    emoji_queue.put(data)
    print('received emoji', data, 'at', time.time())
    return jsonify({"status": "success"}), 200

def batch_and_send():
    # create the producer
    producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    # run an infinite loop that keeps batching and flushing
    while True:
        st = time.time()  # keep track of the start time
        while time.time() < st + 0.5:  # while it has only been less than 500 ms since the start of this iteration
            # read all emojis from the queue and send them via the producer
            while not emoji_queue.empty():
                emoji = emoji_queue.get()
                producer.send('emoji_topic', emoji)
                print('sent emoji', emoji, 'at', time.time())
        # 500 ms have passed now. flush the emoji data
        producer.flush()
        print('flushed in', time.time() - st)

if __name__ == '__main__':
    batch_thread = threading.Thread(target=batch_and_send, daemon=True)
    batch_thread.start()
    app.run(debug=True, port=5000)
