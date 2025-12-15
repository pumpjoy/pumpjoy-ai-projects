# Simulates social media comments

import time
import json
import random
from kafka import KafkaProducer
from faker import Faker

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# A list of crypto-specific terminology to inject into fake tweets
crypto_keywords = ["Bitcoin", "BTC", "Bull run", "Bear market", "HODL", "To the moon", "Crash", "Scam", "Investment"]

def generate_tweet():
    # Inject a crypto keyword into a fake sentence
    keyword = random.choice(crypto_keywords)
    sentence = f"{keyword} {fake.sentence()}"
    
    return {
        'username': fake.user_name(),
        'text': sentence,
        'timestamp': int(time.time() * 1000)
    }

if __name__ == "__main__":
    print("### Generating Social Data ###")
    while True:
        tweet = generate_tweet()
        producer.send('crypto_social', value=tweet)
        print(f"Sent Tweet: {tweet['text']}")
        time.sleep(2) # Send a tweet every 2 seconds