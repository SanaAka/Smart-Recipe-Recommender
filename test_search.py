import requests

response = requests.get("http://127.0.0.1:5000/api/search", params={"query": "Cambodian", "type": "cuisine"})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
