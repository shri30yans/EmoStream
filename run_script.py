import subprocess
import time

def run_code():
    subprocess.Popen([
        'python3', 'app.py',
    ])
    
    subprocess.Popen([
        'python3', 'load_test.py',
    ])
    
    subprocess.Popen([
        'python3', 'spark_processor.py',
    ])
    
    subprocess.Popen([
        'python3', 'main_publisher.py',
    ])
    
# Function to run a producer
def run_producer(topic_name):
    subprocess.Popen([
        'python3', 'cluster_publisher.py',
        '--publisher_topic', topic_name
    ])
    print(f"Started producer for topic: {topic_name}")

# Function to run a subscriber
def run_subscriber(topic_name):
    subprocess.Popen([
        'python3', 'subscriber.py',
        '--subscriber_topic', topic_name
    ])
    print(f"Started subscriber for topic: {topic_name}")

if __name__ == "__main__":
    run_code()
    
    for topic_name in ['subscriber_1', 'subscriber_2', 'subscriber_3']:
        run_producer(topic_name)

        time.sleep(2)

        for i in range(3):
            run_subscriber(topic_name)
            time.sleep(1) 
