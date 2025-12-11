import json
import time
from kafka import KafkaProducer

KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'test_topic'

# value_serializer converts Python object (dict) to JSON bytes
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"Starting producer for topic: {TOPIC_NAME} at {KAFKA_BROKER}")

for i in range(10):
    # Simulate a simple transaction event
    transaction_data = {
        'id': i,
        'timestamp': time.time(),
        'message': f'Test transaction number {i}',
        'status': 'SENT'
    }

    # Produce/Send: Send the data to the topic
    # .get(timeout=10) waits for acknowledgment from Kafka 
    future = producer.send(TOPIC_NAME, value=transaction_data)
    record_metadata = future.get(timeout=10)

    # Logging the success
    print(f"Sent: ID={i} | Topic: {record_metadata.topic} | Partition: {record_metadata.partition} | Offset: {record_metadata.offset}")

    time.sleep(1) # Wait 1 second before sending next message

print("Producer finished sending 10 messages.")
producer.close()