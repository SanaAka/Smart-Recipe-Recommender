import requests
import json

# Test the batch endpoint
url = "http://127.0.0.1:5000/api/recipes/batch"
data = {"recipe_ids": [1, 2, 3]}

print(f"Testing {url}")
print(f"Request data: {json.dumps(data)}")

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
