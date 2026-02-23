import requests
user_id = '6968966ba463d2d4480cbe48'
url = f"http://localhost:8080/favorites"
print(f"Requesting: {url} with params user_id={user_id}")
r = requests.get(url, params={"user_id": user_id})
print(f"Status: {r.status_code}")
print(f"Content: {r.text}")
