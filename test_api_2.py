import requests
user_id = '6968966ba463d2d4480cbe48'
url = f"http://localhost:8080/favorites?user_id={user_id}"
r = requests.get(url)
print(f"Status: {r.status_code}")
print(f"JSON: {r.json()}")
