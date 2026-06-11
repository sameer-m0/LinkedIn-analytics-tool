import httpx

overview_url = "http://127.0.0.1:8000/api/dashboard/overview?preset=last_30"
response = httpx.get(overview_url)
print(f"Status code: {response.status_code}")
print(response.json())
