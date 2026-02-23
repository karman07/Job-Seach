import asyncio
from app.api.jobs import get_favorites
from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

async def main():
    s = get_settings()
    c = AsyncIOMotorClient(s.MONGODB_URL)
    db = c[s.MONGODB_DB_NAME]
    
    user_id = '6968966ba463d2d4480cbe48'
    print(f"Calling get_favorites for {user_id}")
    resp = await get_favorites(user_id=user_id, db=db)
    print(f"Response total: {resp.total}")
    print(f"Jobs: {len(resp.jobs)}")

if __name__ == "__main__":
    asyncio.run(main())
