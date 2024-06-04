import paho.mqtt.client as mqtt
import json
from datetime import datetime
import logging
import numpy as np

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
        
        # Print the received data
        print(json.dumps(data, indent=4))
        
        # Check if data has 120 points and upsample if necessary
        if len(data) == 120:
            data = upsample_data(data, 600)
        
        # Save the data to a JSON file
        save_to_file(data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")

def upsample_data(data, target_length):
    original_length = len(data)
    
    # Generate the original and target indices
    original_indices = np.linspace(0, original_length - 1, original_length)
    target_indices = np.linspace(0, original_length - 1, target_length)
    
    upsampled_data = []
    
    # Interpolate each field
    for field in ['millis', 'gyX', 'gyY', 'gyZ', 'temp']:
        field_values = [point[field] for point in data]
        interpolated_values = np.interp(target_indices, original_indices, field_values)
        
        # Populate the upsampled data
        for i, value in enumerate(interpolated_values):
            if len(upsampled_data) <= i:
                upsampled_data.append({})
            if field == 'millis':
                upsampled_data[i][field] = int(value)  # Ensure millis is an integer
            else:
                upsampled_data[i][field] = value
    
    # Maintain ID and any other fields that are not interpolated
    for point in upsampled_data:
        point['ID'] = data[0]['ID']
    
    logging.info(f"Upsampled data from {original_length} to {target_length} points")
    
    return upsampled_data

def save_to_file(data):
    # Convert int64 to int to ensure JSON serialization
    for item in data:
        for key in item:
            if isinstance(item[key], np.int64):
                item[key] = int(item[key])
    
    filename = "gyro_data.json"
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