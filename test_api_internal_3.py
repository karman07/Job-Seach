import asyncio
from app.api.jobs import get_favorites
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    s = get_settings()
    c = AsyncIOMotorClient(s.MONGODB_URL)
    db = c[s.MONGODB_DB_NAME]
    
    user_id = '6968966ba463d2d4480cbe48'
    print(f"Calling get_favorites for {user_id}")
    resp = await get_favorites(user_id=user_id, db=db)
    print(f"Total: {resp.total}")
    for j in resp.jobs:
        print(f"- {j.job_id}")

if __name__ == "__main__":
    asyncio.run(main())
