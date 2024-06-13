import json
import logging
import os
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Path to save the datasets
DATASET_DIR = "datasets"
os.makedirs(DATASET_DIR, exist_ok=True)

# Global variables to hold collected data and counters
gyro_x = []
gyro_y = []
gyro_z = []
ids = []  # List to hold IDs
current_label = None
dataset_index = {}  # Dictionary to store dataset index for each label

# Label mapping
label_mapping = {
    0: "(1) Berdiri 30 Detik",
    1: "(06) Jalan Mutar 4m",
    2: "(20) Jatuh Depan Coba Duduk",
    3: "(21) Jatuh belakang coba duduk",
    4: "(22) Jatuh samping pas coba duduk"
}

# Function to save data to a file
def save_to_file(gyro_x, gyro_y, gyro_z, ids, label):
    global dataset_index
    filename = os.path.join(DATASET_DIR, f"dataset_label_{label}_{int(time.time())}.json")
    try:
        data = []
        for i in range(len(gyro_x)):
            data_point = {
                'ID': ids[i],  # Use the ID from the MQTT message
                'gyX': gyro_x[i],
                'gyY': gyro_y[i],
                'gyZ': gyro_z[i],
                'label': label
            }
            data.append(data_point)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        
        num_records = len(data)
        print(f"Data saved to {filename} with {num_records} records")
        logging.info(f"Data saved to {filename} with {num_records} records")
        
        # Clear the 'data' variable after saving to file
        data.clear()

        # Reset data counters after saving
        gyro_x.clear()
        gyro_y.clear()
        gyro_z.clear()
        ids.clear()

        # Increment dataset index for this label
        dataset_index[label] += 1
        
    except Exception as e:
        logging.error(f"Failed to save data to file: {e}")

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe("fall-detection/sensor/gyro")

def on_message(client, userdata, msg):
    global gyro_x, gyro_y, gyro_z, ids, current_label, start_time
    
    if current_label is None:
        logging.warning("Received message but no label is selected yet. Ignoring.")
        return
    
    logging.info(f"Message received on topic {msg.topic}")
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        if 'gyX' in data and 'gyY' in data and 'gyZ' in data and 'ID' in data:
            gyro_x.append(data['gyX'])
            gyro_y.append(data['gyY'])
            gyro_z.append(data['gyZ'])
            ids.append(data['ID'])  # Collect the ID from the MQTT message
            
            # Check if time limit (12 seconds) is reached
            if time.time() - start_time >= 12:
                logging.info(f"Time limit reached for label {current_label}")
                # Save collected data
                save_to_file(gyro_x, gyro_y, gyro_z, ids, current_label)
                
                # Prompt for new label input
                new_label_input()

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# Function to prompt for new label input
def new_label_input():
    global current_label, start_time
    while True:
        user_input = input("Enter the label index to start collecting data (or 'q' to quit): ")
        
        if user_input.lower() == 'q':
            print("Exiting data collection...")
            current_label = None
            break

        if user_input.isdigit() and int(user_input) in label_mapping:
            current_label = int(user_input)
            dataset_index[current_label] = dataset_index.get(current_label, 0) + 1  # Increment dataset index for this label
            print(f"Collecting data for label: {label_mapping[current_label]}. Press 's' to stop collection after 12 seconds.")
            
            start_time = time.time()  # Start time for 12 seconds collection
            break
        else:
            print("Invalid input. Please enter a valid label index or 'q' to quit.")

# Main function to start data collection
def main():
    global current_label, dataset_index
    
    print("Press 'Enter' to start data collection for each label and 'q' to quit.")
    while True:
        new_label_input()  # Prompt for initial label input
        
        if current_label is None:
            break
        
        while time.time() - start_time < 12:
            pass  # Wait until 12 seconds are reached
        
        if current_label is not None:
            print(f"Data collection ended for label: {label_mapping[current_label]}")
            print(f"Data collected: {len(gyro_x)} points")
            # Save collected data
            save_to_file(gyro_x, gyro_y, gyro_z, ids, current_label)
            # Reset data lists for the next collection
            gyro_x.clear()
            gyro_y.clear()
            gyro_z.clear()
            ids.clear()

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
