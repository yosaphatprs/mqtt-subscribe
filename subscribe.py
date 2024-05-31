import paho.mqtt.client as mqtt
import json
from datetime import datetime
import numpy as np

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

# Linear interpolation function
def interpolate(data1, data2, factor):
    return data1 + (data2 - data1) * factor

# Upsampling function
def upsample_data(data_list):
    upsampled_data = []
    num_points = len(data_list)
    
    for i in range(num_points - 1):
        data1 = data_list[i]
        data2 = data_list[i + 1]
        
        # Add the first data point
        upsampled_data.append(data1)
        
        # Interpolate 4 additional points between data1 and data2
        for j in range(1, 5):
            factor = j / 5.0
            interpolated_data = {
                "deviceID": data1["deviceID"],
                "timestamp": interpolate(data1["timestamp"], data2["timestamp"], factor),
                "gyroX": interpolate(data1["gyroX"], data2["gyroX"], factor),
                "gyroY": interpolate(data1["gyroY"], data2["gyroY"], factor),
                "gyroZ": interpolate(data1["gyroZ"], data2["gyroZ"], factor),
                "deviceTemperature": interpolate(data1["deviceTemperature"], data2["deviceTemperature"], factor)
            }
            upsampled_data.append(interpolated_data)
    
    # Add the last data point
    upsampled_data.append(data_list[-1])
    
    return upsampled_data

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}")
    try:
        # Parse the JSON data
        data = json.loads(msg.payload.decode())
        
        # Upsample the data
        data_list = data["gyroData"]
        upsampled_data_list = upsample_data(data_list)
        
        # Print the upsampled data
        print(json.dumps(upsampled_data_list, indent=4))
        
        # Save the upsampled data to a JSON file
        save_to_file(upsampled_data_list)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")

def save_to_file(data):
    # Create a filename with the current timestamp
    filename = datetime.now().strftime("gyro_data_%Y%m%d%H%M%S.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")
    print(f"Total number of data points: {len(data)}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("34.143.200.120", 1883, 60)

client.loop_forever()
