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

    try:
        data = json.loads(message)
        # 1. Handle Ping/Pong Protocol (This is often implicit, but explicit is safer)
        # Note: Some libraries handle PING automatically. If yours doesn't, you need to check:
        if 'ping' in data: # Example for a JSON-based stream ping (less common for raw streams)
             ws.send(json.dumps({'pong': data['ping']}))
        # The underlying library might also handle raw PING frames.
        
    except json.JSONDecodeError:
        # If it's not JSON, it might be a raw PING frame from the server (e.g., 'ping')
        # We must explicitly send a PONG back.
        if message == 'ping':
             ws.send('pong')
        # If using a high-level library, it should automatically send PONGs.
        # If using `websocket-client` (which you likely are), you should configure `ping_interval`
        pass # Ignore non-JSON messages if we don't know the format
    

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### Connection Closed ###")

def on_open(ws):
    print("### Connected to Binance on Port 443 ###")
    # Subscribe to Bitcoin/USDT trade stream
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade"],
        "id": 1
    }
    ws.send(json.dumps(subscribe_message))

if __name__ == "__main__":
    # Binance WebSocket URL
    websocket.enableTrace(True)
    import ssl

    socket = "ws://stream.binance.com:80/ws/btcusdt@trade"
    ws = websocket.WebSocketApp(socket,
                                # on_open=on_open,
                                # on_message=on_message,
                                # on_error=on_error,
                                # on_close=on_close
                                )
    print("### Starting Binance connection with TLS override on Port 443 ###")
    ws.run_forever(
        sslopt={"cert_reqs": ssl.CERT_NONE},
        ping_interval=30, # Send a heartbeat ping every 30 seconds
        ping_timeout=10, # If we don't get a pong back in 10s, close and retry
        reconnect=5      # Attempt to reconnect up to 5 times on disconnect
        )