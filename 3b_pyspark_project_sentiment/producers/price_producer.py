# Fetches real Bitcoin pricesimport json

import json
import websocket
from kafka import KafkaProducer

# 1. Configure Kafka Producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_message(ws, message):
    data = json.loads(message)
    # Extract only what we need: Symbol, Price, Timestamp
    payload = {
        'symbol': data['s'],
        'price': float(data['p']),
        'timestamp': data['E']  # Event time
    }
    
    # 2. Send to Kafka
    producer.send('crypto_price', value=payload)
    print(f"Sent Price: {payload['price']}")

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### Connection Closed ###")

def on_open(ws):
    print("### Connected to Binance ###")
    # Subscribe to Bitcoin/USDT trade stream
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade"],
        "id": 1
    }
    ws.send(json.dumps(subscribe_message))

if __name__ == "__main__":
    # Binance WebSocket URL
    socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    ws = websocket.WebSocketApp(socket,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()