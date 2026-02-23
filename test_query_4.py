import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client["jobmatch_db"]
        print("Connected")
        
        colls = await db.list_collection_names()
        print(f"Collections: {colls}")
        
        count = await db.jobs.count_documents({})
        print(f"Jobs count: {count}")
        
        sample = await db.jobs.find_one({})
        print(f"Sample job: {sample['_id'] if sample else 'NONE'}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
