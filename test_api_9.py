import requests
user_id = '6968966ba463d2d4480cbe48'
url = f"http://localhost:8080/698c1eeff55978da5ea2b635/favorite"
payload = {"user_id": user_id}
print(f"Adding favorite via API: {url}")
r = requests.post(url, json=payload)
print(f"Status: {r.status_code}")
print(f"Content: {r.text}")

url_get = f"http://localhost:8080/favorites?user_id={user_id}"
print(f"Getting favorites via API: {url_get}")
r2 = requests.get(url_get)
print(f"Status: {r2.status_code}")
print(f"Content: {r2.text}")
