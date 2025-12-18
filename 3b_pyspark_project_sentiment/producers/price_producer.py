# Fetches real Bitcoin pricesimport json
import time
import pandas as pd
import json
import websocket
from kafka import KafkaProducer

# 1. Configure Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

ts = int(time.time() * 1000)

def on_message(ws, message):
    data = json.loads(message)
    # Coinbase sends a "ticker" type message
    price_data = {
        "symbol": "BTC-USD",
        "price": float(data['price']),
        "timestamp": ts
    }
    producer.send('crypto_price', value=price_data)
    print(f"Coinbase Price: {price_data['price']}")

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### Connection Closed ###")

def on_open(ws):
    # Subscribe to the BTC-USD ticker
    subscribe_msg = {
        "type": "subscribe",
        "channels": [{"name": "ticker", "product_ids": ["BTC-USD"]}]
    }
    ws.send(json.dumps(subscribe_msg))
    print("### Connected to Coinbase WebSocket ###")

if __name__ == "__main__":
    # Coinbase WebSocket URL (Standard port 443)
    socket = "wss://ws-feed.exchange.coinbase.com"
    ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message)
    ws.run_forever()