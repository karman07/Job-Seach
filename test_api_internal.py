import asyncio
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.job_service_mongo import JobService

async def main():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    service = JobService(db)
    
    user_id = '6968966ba463d2d4480cbe48'
    print(f"Calling service for {user_id}")
    jobs = await service.get_user_favorites(user_id)
    print(f"Service returned {len(jobs)} jobs")
    for j in jobs:
        print(f"- {j['_id']}")

if __name__ == "__main__":
    asyncio.run(main())
