import requests
user_id = '6968966ba463d2d4480cbe48'
url = f"http://127.0.0.1:8080/favorites?user_id={user_id}"
print(f"Requesting: {url}")
r = requests.get(url)
print(f"Status: {r.status_code}")
print(f"Content: {r.text}")
