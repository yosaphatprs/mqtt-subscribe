import json
import numpy as np
import logging
import os
import time
from threading import Timer
from tensorflow.keras.models import load_model

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Load the pre-trained model
model = load_model('allnewfall-detect-model.h5')

# Define the interval for predictions (in seconds)
PREDICTION_INTERVAL = 1

# Function to process the JSON data and make predictions
def process_json_data():
    try:
        with open('gyro_data.json', 'r') as f:
            data = json.load(f)

        if len(data) >= 25:  # Ensure we have at least 25 data points
            logging.info("Data has at least 25 points. Making prediction.")
            latest_data = data[-25:]  # Get the last 25 data points
            prediction = make_prediction(latest_data)
            logging.info(f"Prediction: {prediction}")
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
    input_data = input_data.reshape((1, 3, 25, 1))  # Reshape to (1, 3, 25, 1)

    # Make prediction
    prediction = model.predict(input_data)
    return prediction

# Start the first prediction
Timer(PREDICTION_INTERVAL, process_json_data).start()

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Script terminated by user.")
