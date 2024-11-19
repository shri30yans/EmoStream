import streamlit as st
import requests
import time
import random

# Emoji types for selection
EMOJI_TYPES = ["👍", "❤️", "🎉", "😱", "🔥"]
API_ENDPOINT = "http://localhost:5000/emoji"  # Backend endpoint

# Initialize session state for tracking emoji counts
if 'emoji_counts' not in st.session_state:
    st.session_state.emoji_counts = {emoji: 0 for emoji in EMOJI_TYPES}

# Function to simulate backend receiving emoji reactions
def get_emoji_counts():
    """
    Simulate the backend by fetching emoji counts from the backend
    (You can replace this with actual API calls later)
    """
    try:
        response = requests.get("http://localhost:5000/emoji_counts")  # Replace with actual backend URL
        if response.status_code == 200:
            return response.json()  # Assuming the backend returns a JSON dict with emoji counts
        else:
            st.error("Error fetching emoji counts from backend.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return {emoji: random.randint(10, 1000) for emoji in EMOJI_TYPES}  # Simulated response

# Function to simulate client sending emoji reactions
def simulate_client(client_id):
    """
    Simulate sending emojis to the backend
    """
    for _ in range(200):  # Simulate 200 reactions per client
        emoji = random.choice(EMOJI_TYPES)
        payload = {
            "user_id": f"client_{client_id}",
            "emoji_type": emoji,
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload)
            print(f"Client {client_id} sent {emoji}: {response.status_code}")
        except Exception as e:
            print(f"Error for client {client_id}: {e}")
        
        time.sleep(random.uniform(0.01, 0.1))  # Random sleep to simulate real-world behavior

# Simulate multiple clients concurrently
def run_concurrent_clients(num_clients=10):
    """
    Run multiple client threads concurrently
    """
    import threading
    threads = []
    for i in range(num_clients):
        thread = threading.Thread(target=simulate_client, args=(i,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

# Streamlit UI for displaying emoji reactions and sending them
def main():
    st.title("EmoStream: Live Emoji Reactions")
    
    # Initialize session state
    st.header("IPL Match: CSK vs MI")
    
    # Emoji selection
    selected_emoji = st.radio("Select Your Reaction", EMOJI_TYPES)

    # Send emoji button
    if st.button("Send Reaction"):
        payload = {
            "user_id": "user_123",  # Replace with actual user ID
            "emoji_type": selected_emoji,
            "timestamp": time.time()
        }
        try:
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code == 200:
                st.success(f"Sent {selected_emoji} reaction!")
            else:
                st.error("Failed to send emoji.")
        except Exception as e:
            st.error(f"Error sending emoji: {e}")

    # Display live emoji counts
    st.subheader("Live Reactions")
    emoji_counts = get_emoji_counts()  # Fetch the updated counts (simulated)
    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    for i, emoji in enumerate(EMOJI_TYPES):
        with columns[i]:
            st.metric(emoji, emoji_counts.get(emoji, 0))
    
    # Simulate concurrent clients in the background
    if st.button("Simulate Clients"):
        run_concurrent_clients(num_clients=10)  # Start the simulation

if __name__ == "__main__":
    main()
