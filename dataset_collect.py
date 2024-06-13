import json
import logging
import os
import time
from datetime import datetime
from scipy.interpolate import interp1d
import paho.mqtt.client as mqtt
import numpy as np

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Path to save the datasets
DATASET_DIR = "datasets"
os.makedirs(DATASET_DIR, exist_ok=True)

# Global variables to hold collected data and counter
gyro_x = []
gyro_y = []
gyro_z = []
current_label = None
dataset_count = 0
data_counter = 0  # Counter for collected data points

# Label mapping
label_mapping = {
    0: "(1) Berdiri 30 Detik",
    1: "(06) Jalan Mutar 4m",
    2: "(20) Jatuh Depan Coba Duduk",
    3: "(21) Jatuh belakang coba duduk",
    4: "(22) Jatuh samping pas coba duduk"
}

# Function to save data to a file
def save_to_file(gyro_x, gyro_y, gyro_z, label, dataset_index):
    upsampled_data = []
    gyro_x_upsampled = upsample_data(gyro_x)
    gyro_y_upsampled = upsample_data(gyro_y)
    gyro_z_upsampled = upsample_data(gyro_z)

    # Ensure all upsampled arrays are of the same length
    min_len = min(len(gyro_x_upsampled), len(gyro_y_upsampled), len(gyro_z_upsampled))
    gyro_x_upsampled = gyro_x_upsampled[:min_len]
    gyro_y_upsampled = gyro_y_upsampled[:min_len]
    gyro_z_upsampled = gyro_z_upsampled[:min_len]

    for i in range(min_len):
        data_point = {
            'gyX': gyro_x_upsampled[i],
            'gyY': gyro_y_upsampled[i],
            'gyZ': gyro_z_upsampled[i],
            'label': label
        }
        upsampled_data.append(data_point)
    
    filename = os.path.join(DATASET_DIR, f"dataset_label_{label}_{dataset_index}.json")
    try:
        with open(filename, 'w') as f:
            json.dump(upsampled_data, f, indent=4)
        print(f"Data saved to {filename} with {len(upsampled_data)} records")
        logging.info(f"Data saved to {filename} with {len(upsampled_data)} records")
        
        # Print data counter after saving
        global data_counter
        print(f"Data counter: {data_counter}")
        logging.info(f"Data counter: {data_counter}")
        
        # Reset data counter after printing/logging
        data_counter = 0
        
    except Exception as e:
        logging.error(f"Failed to save data to file: {e}")

# Function to upsample data
def upsample_data(data, target_length=1200):
    x = np.linspace(0, 1, len(data))
    f = interp1d(x, data, kind='linear')
    x_new = np.linspace(0, 1, target_length)
    return f(x_new).tolist()

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

def on_message(client, userdata, msg):
    global gyro_x, gyro_y, gyro_z, data_counter
    logging.info(f"Message received on topic {msg.topic}")
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        if 'gyX' in data and 'gyY' in data and 'gyZ' in data:
            gyro_x.append(data['gyX'])
            gyro_y.append(data['gyY'])
            gyro_z.append(data['gyZ'])
            data_counter += 1  # Increment data counter

            # Log the data counter for debugging
            logging.info(f"Data counter: {data_counter}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# Main function to start data collection
def main():
    global current_label, dataset_count, gyro_x, gyro_y, gyro_z
    print("Press 'Enter' to start data collection for each label and 's' to stop.")
    while True:
        user_input = input("Enter the label index to start collecting data (or 'q' to quit): ")
        if user_input.lower() == 'q':
            print("Exiting data collection...")
            break

        if user_input.isdigit() and int(user_input) in label_mapping:
            current_label = int(user_input)
            dataset_count = 0
            print(f"Collecting data for label: {label_mapping[current_label]}. Press 's' to stop collection.")
            
            while True:
                stop_input = input("Press 's' to stop collection: ")
                if stop_input.lower() == 's':
                    print(f"Data collection ended for label: {label_mapping[current_label]}")
                    save_to_file(gyro_x, gyro_y, gyro_z, current_label, dataset_count)
                    # Reset the lists after saving
                    gyro_x, gyro_y, gyro_z = [], [], []
                    dataset_count += 1  # Increment dataset count
                    break
        else:
            print("Invalid input. Please enter a valid label index or 'q' to quit.")

if __name__ == "__main__":
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect("34.143.200.120", 1883, 60)
    client.loop_start()

    main()

    client.loop_stop()
    client.disconnect()
