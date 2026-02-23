import requests
import json

user_id = '6968966ba463d2d4480cbe48'
url = f"http://localhost:8080/favorites?user_id={user_id}"
print(f"Requesting: {url}")
r = requests.get(url)
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")

# Double check if maybe there is another /favorites route
url_2 = f"http://localhost:8080/jobs/favorites?user_id={user_id}"
print(f"Requesting Alternative: {url_2}")
r2 = requests.get(url_2)
print(f"Status Alternative: {r2.status_code}")
