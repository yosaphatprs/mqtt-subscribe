import os
from google.cloud import storage

def upload_to_gcs(local_directory, bucket_name):
    # Initialize Google Cloud Storage client
    client = storage.Client()

    try:
        # Get bucket object
        bucket = client.get_bucket(bucket_name)

        # List local files to upload
        files_to_upload = [f for f in os.listdir(local_directory) if os.path.isfile(os.path.join(local_directory, f))]

        for file_name in files_to_upload:
            local_file_path = os.path.join(local_directory, file_name)
            blob = bucket.blob(file_name)  # Create a new blob in the bucket
            blob.upload_from_filename(local_file_path)  # Upload the file

            print(f"File {file_name} uploaded to {bucket_name}")

    except Exception as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    local_directory = "/home/ecvxevv/fall-detection/mqtt-subscribe/datasets"  # Local directory path containing files to upload
    bucket_name = "group3-falldetection"              # Name of your Google Cloud Storage bucket

    # Upload files to Google Cloud Storage bucket
    upload_to_gcs(local_directory, bucket_name)
