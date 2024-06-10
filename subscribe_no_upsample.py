import paho.mqtt.client as mqtt
import json
from datetime import datetime
import logging
import os

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Directory to save the JSON files
SAVE_DIR = "received_data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

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
        
        # Print the received data
        print(json.dumps(data, indent=4))
        
        # Save the data to a JSON file
        save_to_file(data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")

def save_to_file(data):
    # Convert int64 to int to ensure JSON serialization
    for item in data:
        for key in item:
            if isinstance(item[key], int):
                item[key] = int(item[key])
    
    filename = os.path.join(SAVE_DIR, f"gyro_data_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename} with {len(data)} records")
    logging.info(f"Data saved to {filename} with {len(data)} records")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect("34.143.200.120", 1883, 60)

logging.info("Starting MQTT client loop")
client.loop_forever()