from typing import List
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.services.job_service_mongo import JobService

router = APIRouter()

@router.get("/jobs/engineering-types")
async def get_engineering_job_types(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all unique job types (categories/titles) discovered during sync
    """
    job_service = JobService(db)
    types = await job_service.get_engineering_job_types()
    return {"engineering_types": types}
