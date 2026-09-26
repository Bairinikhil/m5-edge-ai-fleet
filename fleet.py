"""Minimal MQTT fleet registry for M5 edge devices."""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from fastapi import FastAPI

DB_PATH = Path(os.getenv('FLEET_DB', 'fleet.db'))
MQTT_HOST = os.getenv('MQTT_HOST', '127.0.0.1')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'devices/+/+').replace('/+', '/+')
HTTP_HOST = os.getenv('HTTP_HOST', '127.0.0.1')
HTTP_PORT = int(os.getenv('HTTP_PORT', '8082'))
lock = threading.Lock()
app = FastAPI(title='M5 Edge-AI Fleet', version='0.1.0')


def init_db():
    db = sqlite3.connect(DB_PATH)
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS fleet_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          received_at TEXT NOT NULL,
          device_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload_json TEXT NOT NULL
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_fleet_device_time ON fleet_events(device_id, received_at)')
        db.commit()
    finally:
        db.close()


def parse_topic(topic):
    parts = topic.split('/')
    if len(parts) != 3 or parts[0] != 'devices':
        return None
    return parts[1], parts[2]


def store_event(topic, payload):
    parsed_topic = parse_topic(topic)
    if not parsed_topic:
        return False
    device_id, event_type = parsed_topic
    try:
        data = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    payload_device = str(data.get('device_id', device_id))
    if payload_device != device_id:
        return False
    received_at = datetime.now(timezone.utc).isoformat()
    db = sqlite3.connect(DB_PATH)
    try:
        with lock:
            db.execute('INSERT INTO fleet_events(received_at,device_id,event_type,payload_json) VALUES(?,?,?,?)',
                       (received_at, device_id, event_type, json.dumps(data, separators=(',', ':'))))
            db.commit()
    finally:
        db.close()
    return True


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f'MQTT connected: {reason_code}', flush=True)
    client.subscribe(MQTT_TOPIC, qos=1)
    print(f'Subscribed: {MQTT_TOPIC}', flush=True)


def on_message(client, userdata, message):
    if store_event(message.topic, message.payload):
        print(f'Recorded {message.topic}', flush=True)
    else:
        print(f'Ignored invalid fleet event: {message.topic}', flush=True)


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='m5-edge-ai-fleet')
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client


@app.get('/health')
def health():
    with lock:
        db = sqlite3.connect(DB_PATH)
        try:
            count = db.execute('SELECT COUNT(*) FROM fleet_events').fetchone()[0]
            devices = db.execute('SELECT COUNT(DISTINCT device_id) FROM fleet_events').fetchone()[0]
        finally:
            db.close()
    return {'fleet': 'ok', 'events': count, 'devices': devices}


@app.get('/fleet')
def fleet():
    with lock:
        db = sqlite3.connect(DB_PATH)
        try:
            rows = db.execute('''SELECT device_id, event_type, received_at, payload_json
                                 FROM fleet_events WHERE id IN
                                 (SELECT MAX(id) FROM fleet_events GROUP BY device_id, event_type)
                                 ORDER BY device_id, event_type''').fetchall()
        finally:
            db.close()
    return [{'device_id': r[0], 'event_type': r[1], 'received_at': r[2], 'payload': json.loads(r[3])} for r in rows]


def main():
    import uvicorn
    init_db()
    client = start_mqtt()
    try:
        uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()
