
import requests
import sys

def verify_roads_endpoint():
    url = "http://localhost:8000/topology/roads"
    print(f"Testing {url}...")
    
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        print("Failed to connect to server. Ensure it is running.")
        return False
        
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    count = len(data)
    print(f"Total Roads Returned: {count}")
    
    if count != 24:
        print(f"FAIL: Expected 24 roads, got {count}")
        return False
        
    print("PASS: Got 24 roads.")
    return True

if __name__ == "__main__":
    success = verify_roads_endpoint()
    sys.exit(0 if success else 1)
