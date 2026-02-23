import requests
user_id = 'test_new_user'
job_id = '69987d470cbf1267e49d7487'
url_fav = f"http://localhost:8080/{job_id}/favorite"
r_post = requests.post(url_fav, json={"user_id": user_id})
print(f"POST: {r_post.text}")

url_get = f"http://localhost:8080/favorites?user_id={user_id}"
r_get = requests.get(url_get)
print(f"GET: {r_get.text}")
