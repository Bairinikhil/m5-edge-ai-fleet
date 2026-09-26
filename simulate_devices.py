"""Publish safe local fleet fixtures for development and demos."""
import argparse
import json
import time
import paho.mqtt.publish as publish


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--count', type=int, default=3)
    args = parser.parse_args()
    for index in range(1, args.count + 1):
        device_id = f'sim-m5-{index:02d}'
        health = {'device_id': device_id, 'firmware': 'fleet-sim-0.1.0',
                  'uptime_s': 120 + index, 'free_heap': 250000 - index * 100,
                  'wifi_rssi': -40 - index}
        inference = {'device_id': device_id, 'state': ['STILL', 'SHAKING', 'ROTATING'][index % 3],
                     'latency_us': 6, 'model_version': 'tree-v1'}
        ota = {'device_id': device_id, 'status': 'up-to-date', 'firmware': health['firmware']}
        messages = [(f'devices/{device_id}/health', health),
                    (f'devices/{device_id}/inference', inference),
                    (f'devices/{device_id}/ota', ota)]
        for topic, payload in messages:
            publish.single(topic, json.dumps(payload), hostname=args.host, port=args.port, qos=1)
        print(f'Published fixture: {device_id}')
    time.sleep(0.2)


if __name__ == '__main__':
    main()
