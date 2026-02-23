import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["jobmatch_db"]
    
    # Try finding one by one
    ids = ['69987d470cbf1267e49d7482', '69987d470cbf1267e49d7486', '698c1eeff55978da5ea2b635']
    for jid in ids:
        job = await db.jobs.find_one({"_id": jid})
        print(f"Find {jid}: {'FOUND' if job else 'MISSING'}")

if __name__ == "__main__":
    asyncio.run(main())
