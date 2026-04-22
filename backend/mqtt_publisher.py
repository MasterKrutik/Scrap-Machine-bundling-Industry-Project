"""
MQTT Publisher - Simulates IoT sensors on scrap bundle making machines.
Reads sensor_readings.csv and publishes each row as JSON to MQTT broker.

Protocol: MQTT over TCP/IP (port 1883)
Topic pattern: scrap_machine/sensors/{machine_id}
"""

import json
import csv
import time
import os
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
PUBLISH_INTERVAL = 0.05  # seconds between publishes (adjustable)
TOPIC_PREFIX = "scrap_machine/sensors"

DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset", "sensor_readings.csv")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Publisher connected to MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")


def main():
    client = mqtt.Client(client_id="scrap_sensor_publisher")
    client.on_connect = on_connect

    print(f"🔌 Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()

    time.sleep(1)

    print(f"📂 Reading sensor data from {DATASET_PATH}...")

    with open(DATASET_PATH, "r") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            topic = f"{TOPIC_PREFIX}/{row['machine_id']}"
            payload = json.dumps({
                "reading_id": int(row["reading_id"]),
                "machine_id": int(row["machine_id"]),
                "timestamp": row["timestamp"],
                "temperature": float(row["temperature"]),
                "vibration": float(row["vibration"]),
                "pressure": float(row["pressure"]),
                "motor_current": float(row["motor_current"]),
                "oil_level": float(row["oil_level"])
            })

            result = client.publish(topic, payload, qos=1)
            result.wait_for_publish()
            count += 1

            if count % 500 == 0:
                print(f"  📤 Published {count} readings...")

            time.sleep(PUBLISH_INTERVAL)

    print(f"\n✅ Published {count} sensor readings total")
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
