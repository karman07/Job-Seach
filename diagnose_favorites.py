import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_favorites():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    logger.info("Checking favorites collection...")
    favorites = await db.favorites.find({}).to_list(length=100)
    logger.info(f"Found {len(favorites)} favorites")
    
    for fav in favorites:
        user_id = fav.get("user_id")
        job_id = fav.get("job_id")
        logger.info(f"Favorite: User={user_id}, User Type={type(user_id)}, JobID={job_id}, JobID Type={type(job_id)}")
        
        # Try to find the job
        try:
            if isinstance(job_id, str):
                if ObjectId.is_valid(job_id):
                    search_id = ObjectId(job_id)
                else:
                    search_id = job_id # Maybe it's an adzuna_id?
            else:
                search_id = job_id
                
            job = await db.jobs.find_one({"_id": search_id})
            if job:
                logger.info(f"  -> Job found: {job.get('title')}")
            else:
                # Try searching by adzuna_id if it's a string
                job_by_adzuna = await db.jobs.find_one({"adzuna_id": str(job_id)})
                if job_by_adzuna:
                    logger.info(f"  -> Job found by adzuna_id: {job_by_adzuna.get('title')}")
                else:
                    logger.warning(f"  -> Job NOT found for ID {job_id}")
        except Exception as e:
            logger.error(f"  -> Error searching for job {job_id}: {str(e)}")

    logger.info("\nChecking jobs collection samples...")
    jobs = await db.jobs.find({}).limit(5).to_list(length=5)
    for job in jobs:
        logger.info(f"Job: _id={job.get('_id')}, adzuna_id={job.get('adzuna_id')}, title={job.get('title')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(diagnose_favorites())
