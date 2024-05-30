import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}")
    try:
        # Parse the JSON data
        data = json.loads(msg.payload.decode())
        
        # Print the received data
        print(json.dumps(data, indent=4))
        
        # Save the data to a JSON file
        save_to_file(data)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")

def save_to_file(data):
    # Create a filename with the current timestamp
    filename = datetime.now().strftime("gyro_data_%Y%m%d%H%M%S.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.143.200.120", 1883, 60)

client.loop_forever()