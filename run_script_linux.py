import subprocess
import time
import os

def run_in_new_terminal(command):
    subprocess.Popen([
        'gnome-terminal', '--', 'bash', '-c', f"{command}; exec bash"
    ])

def run_code():
    run_in_new_terminal('python3 app.py')
    run_in_new_terminal('python3 load_test.py')
    run_in_new_terminal('python3 spark_processor.py')
    run_in_new_terminal('python3 main_publisher.py')

# Function to run a producer
def run_producer(topic_name):
    run_in_new_terminal(f"python3 cluster_publisher.py --publisher_topic {topic_name}")
    print(f"Started producer for topic: {topic_name}")

# Function to run a subscriber
def run_subscriber(topic_name):
    run_in_new_terminal(f"python3 subscriber.py --subscriber_topic {topic_name}")
    print(f"Started subscriber for topic: {topic_name}")

if __name__ == "__main__":
    run_code()
    run_producer("test")
    run_subscriber("test")
    
    
    
    # for topic_name in ['subscriber_1', 'subscriber_2', 'subscriber_3']:
    #     run_producer(topic_name)

    #     time.sleep(2)

    #     for i in range(3):
    #         run_subscriber(topic_name)
    #         time.sleep(1)
