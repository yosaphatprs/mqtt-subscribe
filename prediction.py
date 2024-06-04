import json
import numpy as np
from tensorflow.keras.models import load_model
import logging

logging.basicConfig(filename='prediction.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

model = load_model('model.h5')

def load_data(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def preprocess_data(data):
    input_data = np.array([[point['gyX'], point['gyY'], point['gyZ'], point['temp']] for point in data])
    input_data = input_data.reshape((1, *input_data.shape))
    return input_data

def handle_predictions(predictions):
    print("Predictions:", predictions)
    logging.info(f"Predictions: {predictions}")

def main():
    filename = "gyro_data.json"
    data = load_data(filename)
    input_data = preprocess_data(data)
    predictions = model.predict(input_data)
    handle_predictions(predictions)

if __name__ == "__main__":
    main()