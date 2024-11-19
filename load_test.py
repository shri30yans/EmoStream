import threading
import requests
import random
import time

def send_emoji():
    url = 'http://localhost:5000/send_emoji'
    emojis = ['smile', 'sad', 'angry', 'love']
    while True:
        data = {
            "user_id": f"user{random.randint(1, 1000)}",
            "emoji_type": random.choice(emojis),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        requests.post(url, json=data)
        time.sleep(0.01)

threads = []
for _ in range(200):
    t = threading.Thread(target=send_emoji)
    t.start()
    threads.append(t)

for t in threads:
    t.join()