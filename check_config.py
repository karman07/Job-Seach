from app.config import get_settings
s = get_settings()
print(f"MONGODB_URL: {s.MONGODB_URL}")
print(f"MONGODB_DB_NAME: {s.MONGODB_DB_NAME}")
