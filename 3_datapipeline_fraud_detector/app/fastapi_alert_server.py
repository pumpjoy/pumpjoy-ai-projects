import json
import threading
import time
from fastapi import FastAPI
from kafka import KafkaConsumer
from typing import List, Dict

# --- CONFIGURATION ---
KAFKA_BROKER = 'localhost:9092' # Connect from host to the EXTERNAL listener
OUTPUT_TOPIC_NAME = 'fraud_alerts'

# --- 1. GLOBAL STATE (In-Memory Alert Store) ---
# Store the last 10 alerts received
alert_store: List[Dict] = []
MAX_ALERTS = 10 

app = FastAPI(title="Real-Time Fraud Alert Server")


# --- 2. KAFKA CONSUMER THREAD ---
def kafka_consumer_thread():
    """Consumes messages from the fraud_alerts topic."""
    consumer = KafkaConsumer(
        OUTPUT_TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest', # Start reading from the latest message
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print(f"Starting FastAPI consumer for topic: {OUTPUT_TOPIC_NAME}")
    
    for message in consumer:
        alert_payload = message.value
        
        # Only store transactions flagged as fraudulent (is_fraud_alert == True)
        if alert_payload.get('is_fraud_alert') == True:
            # Add to the front of the list (newest first)
            alert_store.insert(0, alert_payload) 
            # Trim the store to keep only the latest alerts
            global alert_store
            alert_store = alert_store[:MAX_ALERTS]
            print(f"🚨 NEW FRAUD ALERT: User {alert_payload['user_id']} | Score: {alert_payload['fraud_score']:.4f}")


# --- 3. FASTAPI ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    """Start the Kafka consumer in a background thread when the server starts."""
    threading.Thread(target=kafka_consumer_thread, daemon=True).start()
    print("FastAPI server started and consumer thread initiated.")

@app.get("/alerts/latest", response_model=List[Dict])
def get_latest_alerts():
    """Returns the list of the most recent fraud alerts."""
    return alert_store

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "consumer": "running"}


# Example command to run: uvicorn fastapi_alert_server:app --reload --port 8000