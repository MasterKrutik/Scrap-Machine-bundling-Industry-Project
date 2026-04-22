"""
MQTT Subscriber - Consumes sensor data from MQTT broker and inserts into MySQL.

Protocol: MQTT over TCP/IP (port 1883)
Subscribes to: scrap_machine/sensors/#
"""

import json
import mysql.connector
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "scrap_machine/sensors/#"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "scrap_machine_db"
}

insert_count = 0


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Subscriber connected to MQTT broker")
        client.subscribe(TOPIC, qos=1)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_message(client, userdata, msg):
    global insert_count
    try:
        data = json.loads(msg.payload.decode())
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sensor_readings
            (machine_id, timestamp, temperature, vibration, pressure, motor_current, oil_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["machine_id"],
            data["timestamp"],
            data["temperature"],
            data["vibration"],
            data["pressure"],
            data["motor_current"],
            data["oil_level"]
        ))

        conn.commit()
        cursor.close()
        conn.close()

        insert_count += 1
        if insert_count % 100 == 0:
            print(f"  💾 Inserted {insert_count} readings into MySQL")

    except Exception as e:
        print(f"❌ Error processing message: {e}")


def main():
    client = mqtt.Client(client_id="scrap_sensor_subscriber")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔌 Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, 60)

    print("⏳ Waiting for sensor data... (Ctrl+C to stop)")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"\n✅ Subscriber stopped. Total inserted: {insert_count}")
        client.disconnect()


if __name__ == "__main__":
    main()
