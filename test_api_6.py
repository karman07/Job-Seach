import requests
user_id = '6968966ba463d2d4480cbe48'
url = "http://127.0.0.1:8080/favorites?user_id=6968966ba463d2d4480cbe48"
r = requests.get(url)
print(f"Results: {r.json()}")
