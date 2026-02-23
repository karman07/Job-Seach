import asyncio
import logging
from app.api.jobs import get_favorites
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

# Force logging for the service
logging.basicConfig(level=logging.INFO)

async def main():
    s = get_settings()
    c = AsyncIOMotorClient(s.MONGODB_URL)
    db = c[s.MONGODB_DB_NAME]
    
    uid = '6968966ba463d2d4480cbe48'
    print(f"DEBUGGING API ENDPOINT CALL FOR {uid}")
    resp = await get_favorites(user_id=uid, db=db)
    print(f"RESULT: total={resp.total}, jobs={len(resp.jobs)}")
    for j in resp.jobs:
        print(f" - {j.job_id}: {j.title}")

if __name__ == "__main__":
    asyncio.run(main())
