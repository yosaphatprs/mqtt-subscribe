import json

def count_data_points(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            num_points = len(data)
        else:
            num_points = 1

        print(f"Number of data points: {num_points}")
        return num_points
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return 0
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return 0

if __name__ == "__main__":
    filename = "gyro_data.json"
    count_data_points(filename)
