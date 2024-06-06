import paho.mqtt.client as mqtt
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

# Callback when a message is received
def on_message(client, userdata, msg):
    logging.info(f"Message received on topic {msg.topic}")
    try:
        # Parse the JSON data
        data = json.loads(msg.payload.decode())
        
        # Add timestamp to each data point
        for point in data:
            point['timestamp'] = datetime.now().isoformat()

        # Save the data to a JSON file
        save_to_file(data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")

def save_to_file(data):
    filename = "gyro_data.json"
    try:
        # Read the existing data from the file
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        # If the file does not exist, start with an empty list
        existing_data = []

    # Append the new data
    existing_data.extend(data)

    # Convert int64 to int to ensure JSON serialization
    for item in existing_data:
        for key in item:
            if isinstance(item[key], (int, float)):
                item[key] = item[key]

    # Write the updated data back to the file
    with open(filename, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print(f"Data appended to {filename} with {len(data)} new records")
    logging.info(f"Data appended to {filename} with {len(data)} new records")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect("34.143.200.120", 1883, 60)

logging.info("Starting MQTT client loop")
client.loop_forever()