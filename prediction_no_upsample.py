import json
import numpy as np
import logging
import os
import time
import psycopg2
from threading import Timer
from tensorflow.keras.models import load_model
import paho.mqtt.client as mqtt

# Setup logging
logging.basicConfig(filename='mqtt_client.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Load the pre-trained model
model = load_model('new_model.h5')

# Define the interval for predictions (in seconds)
PREDICTION_INTERVAL = 0.5

# Label mapping
label_mapping = {
    0: "(1) Berdiri 30 Detik",
    1: "(06) Jalan Mutar 4m",
    2: "(20) Jatuh Depan Coba Duduk",
    3: "(21) Jatuh belakang coba duduk",
    4: "(22) Jatuh samping pas coba duduk"
}

# MQTT broker settings for sending prediction messages
MQTT_BROKER_PREDICTION = "34.101.195.105"
MQTT_PORT = 1883
MQTT_TOPIC = "teddy_belt/notifications"

# PostgreSQL database connection settings
DB_NAME = "fall_detection"
DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = "5432"

# Connect to PostgreSQL database
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

# Save falling event to the database
def save_falling_event(label):
    conn = connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO fall_events (label) VALUES (%s)",
                (label,)
            )
            conn.commit()
            cur.close()
            logging.info(f"Falling event saved: {label}")
        except Exception as e:
            logging.error(f"Failed to save falling event to the database: {e}")
        finally:
            conn.close()

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

            # If predicted class index is 2, 3, or 4, publish to MQTT and save to database
            if predicted_class_index in [2, 3, 4]:
                msg = ""
                if predicted_class_index == 2:
                    msg = "Jatuh Depan Coba Duduk"
                elif predicted_class_index == 3:
                    msg = "Jatuh Belakang Coba Duduk"
                elif predicted_class_index == 4:
                    msg = "Jatuh Samping Pas Coba Duduk"
                mqtt_client.publish(MQTT_TOPIC, msg)
                save_falling_event(predicted_label)
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

# MQTT setup for publishing messages from prediction
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT broker at {MQTT_BROKER_PREDICTION}")
    else:
        logging.error(f"Failed to connect to MQTT broker, return code {rc}")

mqtt_client.on_connect = on_connect

try:
    mqtt_client.connect(MQTT_BROKER_PREDICTION, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    logging.error(f"Failed to connect to MQTT broker: {e}")

# Start the first prediction
Timer(PREDICTION_INTERVAL, process_json_data).start()

# Keep the script running
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    logging.info("Script terminated by user.")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
