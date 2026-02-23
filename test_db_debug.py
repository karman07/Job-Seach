import asyncio
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug")

async def main():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    user_id = '6968966ba463d2d4480cbe48'
    logger.info(f"Checking user: {user_id}")
    
    favs = await db.favorites.find({"user_id": user_id}).to_list(100)
    logger.info(f"Found {len(favs)} favorites in collection")
    
    ids = [f['job_id'] for f in favs]
    logger.info(f"Target IDs: {ids}")
    
    # Method 1: $in query
    jobs_in = await db.jobs.find({"_id": {"$in": ids}}).to_list(100)
    logger.info(f"Method 1 ($in) found: {len(jobs_in)}")
    
    # Method 2: loop find_one
    jobs_loop = []
    for jid in ids:
        j = await db.jobs.find_one({"_id": jid})
        if j:
            jobs_loop.append(j)
    logger.info(f"Method 2 (loop) found: {len(jobs_loop)}")
    
    # Verify first ID specifically
    if ids:
        first_id = ids[0]
        count = await db.jobs.count_documents({"_id": first_id})
        logger.info(f"Count for {first_id}: {count}")

if __name__ == "__main__":
    asyncio.run(main())
