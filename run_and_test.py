import subprocess
import time
import requests
import json
import sys

def start_server():
    print("Starting Flask server...")
    server_process = subprocess.Popen(
        ["python", "api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Give the server time to start
    return server_process

def test_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print("\nRoot endpoint test:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
        return False

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print("\nHealth endpoint test:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing health endpoint: {e}")
        return False

    # Test recommend endpoint
    try:
        data = {
            "query": "personality test",
            "top_k": 3
        }
        response = requests.post(
            f"{base_url}/recommend",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print("\nRecommend endpoint test:")
        print(f"Status: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error testing recommend endpoint: {e}")
        return False

    return True

if __name__ == "__main__":
    server_process = start_server()
    try:
        success = test_endpoints()
        if success:
            print("\nAll tests completed successfully!")
        else:
            print("\nSome tests failed!")
    finally:
        print("\nStopping server...")
        server_process.terminate()
        sys.exit(0 if success else 1)