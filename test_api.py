import requests

url = "http://localhost:8000/api/leads/discover"
payload = {
    "sector": "Hospital",
    "location": "Noida",
    "max_pages": 1,
    "max_runtime_seconds": 20
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
