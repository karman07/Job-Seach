import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    # settings = get_settings()
    # Manual connection to be sure
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["jobmatch_db"]
    
    ids = ['69987d470cbf1267e49d7482', '69987d470cbf1267e49d7486', '698c1eeff55978da5ea2b635']
    query = {"_id": {"$in": ids}}
    print(f"Query: {query}")
    
    results = await db.jobs.find(query).to_list(length=10)
    print(f"Results: {len(results)}")
    for r in results:
        print(f"Found: {r['_id']} - {r['title']}")

if __name__ == "__main__":
    asyncio.run(main())
