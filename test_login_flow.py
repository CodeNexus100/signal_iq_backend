
import requests
import random
import string
import json
import sys

# Try 127.0.0.1 to avoid potential localhost IPv6 issues
port = sys.argv[1] if len(sys.argv) > 1 else "8000"
BASE_URL = f"http://127.0.0.1:{port}"

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def run_test():
    # 1. Generate random user credentials
    username = f"user_{get_random_string(6)}"
    email = f"{username}@test.com"
    password = "password123"
    role = "ADMIN"

    print(f"Testing with: {username} / {email}")

    # 2. Register
    register_payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    
    print("\n[1] Registering user...")
    try:
        reg_response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
        reg_response.raise_for_status()
        print("Registration Successful")
        print(json.dumps(reg_response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Registration Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(e.response.text)
        return

    # 3. Login
    login_payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }

    print("\n[2] Logging in...")
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        login_response.raise_for_status()
        data = login_response.json()
        
        # Verify structure
        if "accessToken" in data and "user" in data:
            print("Login Successful")
            print("Received Token:", data["accessToken"][:20] + "...")
            print("User Data:", json.dumps(data["user"], indent=2))
        else:
            print("Login Failed: Unexpected response structure")
            print(json.dumps(data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Login Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

if __name__ == "__main__":
    print(f"Connecting to {BASE_URL}...")
    try:
        requests.get(f"{BASE_URL}/health")
        run_test()
    except Exception as e:
        print(f"Could not connect to backend server: {e}")
