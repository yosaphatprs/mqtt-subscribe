import json
import numpy as np
import logging
import os
import time
from threading import Timer
from tensorflow.keras.models import load_model
import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Load the pre-trained model
model = load_model('new_model.h5')

# Define the interval for predictions (in seconds)
PREDICTION_INTERVAL = 1

# Label mapping
label_mapping = {
    0: "(1) Berdiri 30 Detik",
    1: "(06) Jalan Mutar 4m",
    2: "(20) Jatuh Depan Coba Duduk",
    3: "(21) Jatuh belakang coba duduk",
    4: "(22) Jatuh samping pas coba duduk"
}

# MQTT settings
MQTT_BROKER = "34.101.195.105"
MQTT_PORT = 1883
MQTT_TOPIC = "teddy_belt/notifications"
MQTT_TIMEOUT = 120  # Increased timeout

# Create an MQTT client instance
mqtt_client = mqtt.Client()

def connect_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_TIMEOUT)
        logging.info("Connected to MQTT broker")
    except Exception as e:
        logging.error(f"Failed to connect to MQTT broker: {e}")

# Try to connect to the MQTT broker
connect_mqtt()

# Function to process the JSON data and make predictions
def process_json_data():
    try:
        with open('gyro_data.json', 'r') as f:
            data = json.load(f)

        if len(data) >= 120:  # Ensure we have at least 120 data points
            logging.info("Data has at least 120 points. Making prediction.")
            latest_data = data[-120:]  # Get the last 120 data points
            prediction, predicted_label, predicted_class_index = make_prediction(latest_data)
            logging.info(f"Prediction: {prediction}, Predicted Class: {predicted_label}")
            print(f"Prediction: {prediction}, Predicted Class: {predicted_label}")

            # Only attempt to send MQTT notification if connected
            if mqtt_client.is_connected() and predicted_class_index in [2, 3, 4]:
                send_mqtt_notification(predicted_label)
    except Exception as e:
        logging.error(f"Error processing JSON data: {e}")

    # Schedule the next prediction
    Timer(PREDICTION_INTERVAL, process_json_data).start()

def make_prediction(data):
    # Extract relevant fields and reshape for prediction
    gyro_x = [point['gyX'] for point in data]
    gyro_y = [point['gyY'] for point in data]
    gyro_z = [point['gyZ'] for point in data]

    # Reshape data for model prediction
    input_data = np.array([gyro_x, gyro_y, gyro_z])
    input_data = input_data.reshape((1, 3, 120, 1))  # Reshape to (1, 3, 120, 1)

    # Make prediction
    prediction = model.predict(input_data)
    predicted_class_index = np.argmax(prediction, axis=1)[0]
    predicted_label = label_mapping[predicted_class_index]
    
    return prediction, predicted_label, predicted_class_index

def send_mqtt_notification(label):
    try:
        msg = ""
        if label == 2:
            msg = "Jatuh Depan Coba Duduk"
        elif label == 3:
            msg = "Jatuh Belakang Coba Duduk"
        elif label == 4:
            msg = "Jatuh Samping Pas Coba Duduk"
        mqtt_client.publish(MQTT_TOPIC, msg)
        logging.info(f"Sent MQTT notification: {label}")
    except Exception as e:
        logging.error(f"Failed to send MQTT notification: {e}")

# Start the first prediction
Timer(PREDICTION_INTERVAL, process_json_data).start()

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Script terminated by user.")
    mqtt_client.disconnect()
