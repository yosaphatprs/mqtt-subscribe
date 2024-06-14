import os
from google.cloud import storage

# Path to your JSON key file
JSON_KEY_PATH = '/path/to/your/json/key.json'

# Initialize a client using JSON key for authentication
client = storage.Client.from_service_account_json(JSON_KEY_PATH)

def upload_to_gcs(bucket_name, source_folder):
    bucket = client.get_bucket(bucket_name)

    for root, _, files in os.walk(source_folder):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            blob_name = os.path.relpath(local_file_path, source_folder)
            
            # Upload file with JSON metadata
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_file_path, content_type='application/json')

            print(f"File {file_name} uploaded to {bucket_name} as {blob_name}")

if __name__ == "__main__":
    source_folder = "/home/ecvxevv/fall-detection/mqtt-subscribe/datasets"  # Local directory path containing files to upload
    bucket_name = "group3-falldetection"    

    upload_to_gcs(bucket_name, source_folder)
