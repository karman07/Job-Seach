import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

async def main():
    s = get_settings()
    c = AsyncIOMotorClient(s.MONGODB_URL)
    db = c[s.MONGODB_DB_NAME]
    
    uid = '6968966ba463d2d4480cbe48'
    favs = await db.favorites.find({'user_id': uid}).to_list(100)
    print(f"FAVORITES IN DB: {len(favs)}")
    for f in favs:
        print(f" - {f}")
        
    jobs = await db.jobs.find({'_id': {'$in': [f['job_id'] for f in favs]}}).to_list(100)
    print(f"JOBS IN DB: {len(jobs)}")
    for j in jobs:
        print(f" - {j['_id']}")

if __name__ == "__main__":
    asyncio.run(main())
