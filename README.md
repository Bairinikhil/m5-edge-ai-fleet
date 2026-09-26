# M5 Edge-AI Fleet

The final roadmap project: a small fleet control plane for M5 edge devices. It receives health, inference, and OTA status events over MQTT, stores the latest fleet history in SQLite, and exposes a local API.

## Current milestone

```text
M5 devices → MQTT → fleet registry → SQLite → fleet API
```

The first milestone supports:

- Multiple device IDs
- Health events at `devices/<device_id>/health`
- Inference events at `devices/<device_id>/inference`
- OTA events at `devices/<device_id>/ota`
- Device identity validation
- Latest event view at `GET /fleet`
- Fleet health at `GET /health`

No commands or firmware updates are sent yet. The service is local-only by default.

Smoke-tested with the real `m5-device-01` plus three simulated devices: **12 events**, **4 devices**, and health/inference/OTA records visible through `/fleet`.

## Run with WSL2

```bash
cd /mnt/d/m5-edge-ai-fleet
python3 -m venv ~/m5-fleet-venv
source ~/m5-fleet-venv/bin/activate
pip install -r requirements.txt

export MQTT_HOST=192.168.1.156
export MQTT_PORT=1883
python fleet.py
```

The API runs at `http://127.0.0.1:8082`.

## Test with simulated devices

In a second Ubuntu terminal:

```bash
source ~/m5-fleet-venv/bin/activate
cd /mnt/d/m5-edge-ai-fleet
python simulate_devices.py --host 192.168.1.156 --port 1883 --count 3
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8082/fleet
```

The simulator creates three safe development fixtures; it does not touch the M5 or change firmware.

## Checks

```bash
python -m unittest -v
```

Next milestones are a fleet dashboard, authenticated commands, signed OTA rollout tracking, reconnect/offline detection, and a TLS-only deployment profile.
