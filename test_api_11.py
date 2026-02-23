import requests
import json

u1 = "http://localhost:8080/favorites?user_id=6968966ba463d2d4480cbe48"
u2 = "http://127.0.0.1:8080/favorites?user_id=6968966ba463d2d4480cbe48"

print(f"U1 ({u1}): {requests.get(u1).text}")
print(f"U2 ({u2}): {requests.get(u2).text}")
