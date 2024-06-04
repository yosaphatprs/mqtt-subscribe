import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import logging
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Load the pre-trained model
model = load_model('model.h5')

# Define the handler to process file changes
class JsonFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == "gyro_data.json":
            logging.info(f"{event.src_path} has been modified")
            process_json_data(event.src_path)

def process_json_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if len(data) == 600:  # Ensure we have the correct number of data points
        logging.info("Data has 600 points. Making prediction.")
        prediction = make_prediction(data)
        logging.info(f"Prediction: {prediction}")

def make_prediction(data):
    # Extract relevant fields and reshape for prediction
    gyro_x = [point['gyX'] for point in data]
    gyro_y = [point['gyY'] for point in data]
    gyro_z = [point['gyZ'] for point in data]

    # Reshape data for model prediction
    input_data = np.array([gyro_x, gyro_y, gyro_z]).T
    input_data = input_data.reshape(1, input_data.shape[0], input_data.shape[1])

    # Make prediction
    prediction = model.predict(input_data)
    return prediction

# Setup the watchdog observer
event_handler = JsonFileHandler()
observer = Observer()
observer.schedule(event_handler, path='.', recursive=False)
observer.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    observer.stop()
observer.join()