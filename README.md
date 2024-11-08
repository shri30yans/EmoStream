# EC-Team-74-emostream-concurrent-emoji-broadcast-over-event-driven-architecture

# EmoStream: Concurrent Emoji Broadcast over Event-Driven Architecture

## Project Overview
EmoStream captures and broadcasts real-time emoji reactions from fans during live events, such as sporting matches, to reflect the collective sentiment of the audience. This system addresses the challenge of processing billions of emojis with low latency and high concurrency, creating an engaging and responsive viewer experience on platforms like Hotstar.

## Goal
The primary objective of EmoStream is to design a horizontally scalable architecture that can process billions of user-generated emojis per second. Using an event-driven approach, EmoStream leverages frameworks such as **Apache Kafka** for efficient data streaming and **Apache Spark** for real-time processing, ensuring seamless delivery of real-time emoji aggregations back to the users.

## Architecture Overview

### 1. Receiving Emoji Data from Clients
- **API Endpoint**: A lightweight HTTP endpoint (built with Flask or Express.js) receives POST requests containing user emoji data, including:
  - **User ID**, **Emoji Type**, **Timestamp**
- **Kafka Producer**: The data from the endpoint is sent asynchronously to a Kafka producer, which queues and flushes the data at 500-millisecond intervals to a Kafka broker.

### 2. Processing Emoji Data in Real-Time
- **Data Aggregation**: A Kafka consumer continuously consumes emoji data from the Kafka broker, and **Apache Spark** processes it in micro-batches with a 2-second interval to provide real-time insights.
- **Aggregation Algorithm**: Emojis are aggregated over each interval, condensing up to 1000 identical emojis into a single count to represent the volume of similar reactions, which reduces data size and improves response time.

### 3. Broadcasting Processed Data to Clients
- **Publisher-Subscriber Model**: EmoStream employs a Pub-Sub architecture for scaling to support numerous clients.
  - **Main Publisher**: Receives processed emoji data from Spark and distributes it to cluster publishers.
  - **Clusters**: Each cluster consists of a **Cluster Publisher** and multiple **Subscribers**.
  - **Subscribers**: Clients are registered to specific subscribers to receive real-time emoji data updates, ensuring efficient load distribution and high concurrency.

## Final Deliverables
- **API Endpoint**: An endpoint to receive emoji POST requests from clients and queue them in Kafka.
- **Kafka Producer**: Sends buffered emoji data to Kafka at regular 500-millisecond intervals.
- **Spark Streaming Job**: Processes emoji data in 2-second micro-batches with aggregation to optimize data flow.
- **Pub-Sub System**: A scalable Pub-Sub model supporting numerous clients with real-time updates.
- **Testing**:
  - **Unit Tests**: For API endpoints and message queue reliability.
  - **Load Tests**: To confirm system performance under high concurrency.

## Demo Overview
1. Multiple clients send emoji data to the API endpoint in real-time.
2. Kafka producer asynchronously queues emojis and flushes them to Kafka broker.
3. Spark processes data in 2-second intervals, aggregates emoji counts, and passes results to the main publisher.
4. The Pub-Sub architecture distributes aggregated data back to clients through cluster publishers and subscribers, providing a seamless experience.

## References
- [Hotstar’s Architecture for Live Streaming](https://highscalability.com/capturing-a-billion-emo-j-i-ons/)
- [Building Scalable Pub-Sub Systems](https://newsletter.systemdesign.one/p/hotstar-architecture)
- [YouTube: ByteByteGo on Event-Driven Architecture](https://www.youtube.com/watch?v=UN1kW5AHid4)

EmoStream offers a high-performance, event-driven solution for handling real-time user-generated content, transforming user reactions into a dynamic display of crowd sentiment in live broadcast experiences.
