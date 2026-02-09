
import requests
import sys
import time

def verify_signal_endpoint():
    url = "http://localhost:8000/traffic/signal/I00"
    print(f"Testing {url}...")
    
    # Wait for server to start
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is up!")
                break
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/{max_retries})")
            time.sleep(1)
    else:
        print("Failed to connect to server.")
        return False

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    print("Response JSON:")
    print(data)
    
    expected_keys = {
        "intersection_id": str,
        "active_axis": str,
        "green_time": int,
        "red_time": int,
        "level": str,
        "downstream_blocked": bool
    }
    
    errors = []
    for key, type_ in expected_keys.items():
        if key not in data:
            errors.append(f"Missing key: {key}")
        elif not isinstance(data[key], type_):
            errors.append(f"Incorrect type for {key}: expected {type_}, got {type(data[key])}")
            
    if data.get("active_axis") not in ["X", "Z"]:
         errors.append(f"Invalid active_axis: {data.get('active_axis')}")

    if data.get("level") not in ["LOW", "MEDIUM", "HIGH"]:
         errors.append(f"Invalid level: {data.get('level')}")

    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return False
    
    print("Validation PASSED.")
    return True

if __name__ == "__main__":
    success = verify_signal_endpoint()
    sys.exit(0 if success else 1)
