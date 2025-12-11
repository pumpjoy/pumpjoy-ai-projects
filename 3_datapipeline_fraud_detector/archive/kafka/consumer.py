import json
from kafka import KafkaConsumer

KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'test_topic'

# Ensures that if run multiple consumers, 
# they load-balance reading from the partitions.
CONSUMER_GROUP_ID = 'test_group'

# value_deserializer converts JSON bytes back into a Python dictionary
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest', 
    enable_auto_commit=True,
    group_id=CONSUMER_GROUP_ID,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print(f"Starting consumer for topic: {TOPIC_NAME} in group: {CONSUMER_GROUP_ID}")
print("Waiting for messages...")

# The consumer continually polls for new messages
for message in consumer:
    print("--- Received Message ---")
    print(f"Topic: {message.topic} | Partition: {message.partition} | Offset: {message.offset}")
    print(f"Value: {message.value}")
    
    # DEBUG: Exit after processing 10 messages 
    if message.value.get('id', -1) == 9: 
        print("Processed last message. Exiting.")
        break