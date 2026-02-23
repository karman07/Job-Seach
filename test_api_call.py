import requests

def test():
    user_id = '6968966ba463d2d4480cbe48'
    url = f"http://localhost:8080/favorites?user_id={user_id}"
    print(f"Calling: {url}")
    resp = requests.get(url)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json()}")

if __name__ == "__main__":
    test()
