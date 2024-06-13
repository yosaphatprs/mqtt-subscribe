import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Path to save the JSON file
SAVE_FILE = "gyro_data.json"  # Assuming current directory is fine

# Maximum number of data points to store
MAX_DATA_POINTS = 1200

# Load existing data if the file exists
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, 'r') as f:
        try:
            data_list = json.load(f)
        except json.JSONDecodeError:
            data_list = []
else:
    data_list = []

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

# Callback when a message is received
def on_message(client, userdata, msg):
    logging.info(f"Message received on topic {msg.topic}")
    try:
        # Unpack the binary data
        payload = msg.payload
        if len(payload) == 13:
            device_id = chr(payload[0])
            gyX, gyY, gyZ = struct.unpack('fff', payload[1:])
            
            # Prepare the data point as a dictionary
            data_point = {
                'ID': device_id,
                'gyX': gyX,
                'gyY': gyY,
                'gyZ': gyZ,
                'timestamp': datetime.now().isoformat()
            }
            
            # Print the received data (optional)
            print(json.dumps(data_point, indent=4))
            
            # Add the new data point to the list
            data_list.append(data_point)
            
            # Ensure the list does not exceed MAX_DATA_POINTS
            if len(data_list) > MAX_DATA_POINTS:
                data_list.pop(0)
            
            # Save the updated data list to the JSON file
            save_to_file(data_list)
        else:
            logging.error("Received payload has unexpected length")
    except struct.error as e:
        logging.error(f"Failed to unpack binary data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def save_to_file(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {SAVE_FILE} with {len(data)} records")
        logging.info(f"Data saved to {SAVE_FILE} with {len(data)} records")
    except Exception as e:
        logging.error(f"Failed to save data to file: {e}")
        print(f"Failed to save data to file: {e}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect("34.143.200.120", 1883, 60)

logging.info("Starting MQTT client loop")
client.loop_forever()
