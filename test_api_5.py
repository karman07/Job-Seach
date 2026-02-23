import requests
user_id = '6968966ba463d2d4480cbe48'
url = "http://localhost:8080/health"
r = requests.get(url)
print(f"Health: {r.json()}")
