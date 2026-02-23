import requests
import json

u = "http://localhost:8080/jobs?limit=1"
print(f"Jobs: {requests.get(u).text}")
