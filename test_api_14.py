import requests
job_id = '69987d470cbf1267e49d7487'
url = f"http://localhost:8080/{job_id}/favorite"
r = requests.post(url, json={"user_id": "test_user"})
print(f"URL: {url}")
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
