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
    global data_counter
    filename = os.path.join(DATASET_DIR, f"dataset_label_{label}_{dataset_index}.json")
    try:
        data = {
            'gyro_x': gyro_x,
            'gyro_y': gyro_y,
            'gyro_z': gyro_z,
            'label': label
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        num_records = len(gyro_x)  # Assuming gyro_x, gyro_y, and gyro_z have the same length
        print(f"Data saved to {filename} with {num_records} records")
        logging.info(f"Data saved to {filename} with {num_records} records")
        
        # Print data counter after saving
        print(f"Data counter: {data_counter}")
        logging.info(f"Data counter: {data_counter}")
        
        # Reset data counter after printing/logging
        data_counter = 0
        
    except Exception as e:
        logging.error(f"Failed to save data to file: {e}")

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
    print("Press 'Enter' to start data collection for each label and 'q' to quit.")
    while True:
        user_input = input("Enter the label index to start collecting data (or 'q' to quit): ")
        if user_input.lower() == 'q':
            print("Exiting data collection...")
            break

        if user_input.isdigit() and int(user_input) in label_mapping:
            current_label = int(user_input)
            dataset_count = 0
            print(f"Collecting data for label: {label_mapping[current_label]}. Press 's' to stop collection after 12 seconds.")
            
            start_time = time.time()
            while time.time() - start_time < 12:
                pass  # Collect data for 12 seconds
            
            print(f"Data collection ended for label: {label_mapping[current_label]}")
            print(f"Data collected: {data_counter} points")
            # Save collected data
            save_to_file(gyro_x, gyro_y, gyro_z, current_label, dataset_count)
            # Reset data lists and counters
            gyro_x, gyro_y, gyro_z = [], [], []
            dataset_count += 1  # Increment dataset count

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
