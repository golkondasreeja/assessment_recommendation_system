import requests
import json

BASE_URL = "http://localhost:8000"

def test_root():
    response = requests.get(f"{BASE_URL}/")
    print("\nTesting root endpoint:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("\nTesting health endpoint:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_recommendations(query, top_k=3):
    data = {
        "query": query,
        "top_k": top_k
    }
    response = requests.post(
        f"{BASE_URL}/recommend",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print(f"\nTesting recommendations for query: '{query}'")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    # Test basic endpoints
    test_root()
    test_health()
    
    # Test different recommendation queries
    test_queries = [
        "personality test",
        "video interview",
        "skills assessment",
        "360 feedback"
    ]
    
    for query in test_queries:
        test_recommendations(query) 