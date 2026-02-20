from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging
from app.database import get_db
from app.schemas import RefreshJobsResponse
from app.services.job_service_mongo import JobService
from app.scheduler import get_scheduler
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/admin/refresh-jobs", response_model=RefreshJobsResponse)
async def refresh_jobs_manually(
    background_tasks: BackgroundTasks,
    search_query: str = None,
    max_pages: int = 20,
    country: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger job refresh from Adzuna
    
    This endpoint triggers an immediate sync of jobs from Adzuna to the database.
    The sync runs asynchronously in the background.
    
    Returns immediately with a sync ID that can be used to track progress.
    """
    try:
        logger.info(f"Manual job refresh triggered via API for query: {search_query}, country: {country}")
        
        # Run in background using FastAPI BackgroundTasks
        job_service = JobService(db)
        
        # Start sync asynchronously
        async def sync_task():
            if search_query == "ALL_ENGINEERING":
                logger.info("Starting mass sync via sync_engineering_jobs...")
                await job_service.sync_engineering_jobs()
            else:
                await job_service.sync_jobs_from_adzuna(
                    sync_type="manual",
                    max_pages=max_pages,
                    search_query=search_query,
                    country=country
                )
        
        background_tasks.add_task(sync_task)
        
        return RefreshJobsResponse(
            message=f"Job refresh for '{search_query}' initiated successfully",
            sync_id=0,  # Will be generated when task runs
            status="in_progress"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger job refresh: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger job refresh: {str(e)}"
        )


@router.post("/admin/refresh-jobs-multi-region", response_model=RefreshJobsResponse)
async def refresh_jobs_multi_region_manually(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger multi-region engineering job refresh.
    Ratios: US (70%), India (15%), GB/CA/AU (15%)
    """
    try:
        logger.info("Multi-region manual job refresh triggered via API")
        
        job_service = JobService(db)
        
        # Start sync asynchronously
        background_tasks.add_task(job_service.sync_multi_region_engineering_jobs)
        
        return RefreshJobsResponse(
            message="Multi-region job refresh initiated successfully",
            sync_id=0,
            status="in_progress"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger multi-region job refresh: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger multi-region job refresh: {str(e)}"
        )


@router.post("/admin/clear-cache")
async def clear_cache(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Clear all cached resume search results"""
    try:
        result = await db.resume_search_cache.delete_many({})
        return {
            "message": "Cache cleared successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats")
async def get_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get database statistics"""
    try:
        total_jobs = await db.jobs.count_documents({})
        active_jobs = await db.jobs.count_documents({"status": "active"})
        cache_entries = await db.resume_search_cache.count_documents({})
        
        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "cached_searches": cache_entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/sync-to-cts")
async def sync_all_jobs_to_cts(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Sync all existing MongoDB jobs to Google Cloud Talent Solution
    
    This utility creates CTS entries for jobs that don't have them yet.
    Useful after enabling CTS permissions or migrating data.
    """
    try:
        from app.integrations.cts import CTSClient
        from datetime import datetime
        
        async def sync_task():
            cts_client = CTSClient()
            jobs_collection = db.jobs
            
            # Find jobs without CTS job name (not yet synced to CTS)
            cursor = jobs_collection.find({
                "$or": [
                    {"cts_job_name": None},
                    {"cts_job_name": {"$exists": False}}
                ],
                "status": "active"
            })
            
            jobs_to_sync = await cursor.to_list(length=None)
            total_jobs = len(jobs_to_sync)
            
            logger.info(f"Starting CTS sync for {total_jobs} jobs")
            
            success_count = 0
            failed_count = 0
            
            for job in jobs_to_sync:
                try:
                    # Prepare job data for CTS
                    job_data = {
                        "adzuna_id": job["adzuna_id"],
                        "title": job["title"],
                        "description": job["description"],
                        "company_display_name": job.get("company_display_name", "Unknown Company"),
                        "location": job.get("location"),
                        "location_structured": job.get("location_structured"),
                        "employment_type": job.get("employment_type"),
                        "job_level": job.get("job_level"),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "category": job.get("category"),
                        "redirect_url": job.get("redirect_url"),
                        "is_internship": job.get("is_internship", False)
                    }
                    
                    # Create in CTS
                    cts_job_name = cts_client.create_job(job_data)
                    
                    # Update MongoDB with CTS info
                    await jobs_collection.update_one(
                        {"_id": job["_id"]},
                        {
                            "$set": {
                                "cts_job_name": cts_job_name,
                                "last_synced_to_cts": datetime.utcnow()
                            }
                        }
                    )
                    
                    success_count += 1
                    
                    if success_count % 10 == 0:
                        logger.info(f"CTS sync progress: {success_count}/{total_jobs} jobs synced")
                    
                except Exception as e:
                    failed_count += 1
                    # Log full stack trace to expose AttributeError or other programming errors
                    logger.exception(f"Failed to sync job {job['adzuna_id']} to CTS: {str(e)}")
                    continue
            
            logger.info(f"CTS sync completed: {success_count} successful, {failed_count} failed out of {total_jobs} total")
        
        background_tasks.add_task(sync_task)
        
        # Count jobs to sync
        total_to_sync = await db.jobs.count_documents({
            "$or": [
                {"cts_job_name": None},
                {"cts_job_name": {"$exists": False}}
            ],
            "status": "active"
        })
        
        return {
            "message": "CTS sync initiated",
            "jobs_to_sync": total_to_sync,
            "status": "in_progress"
        }
        
    except Exception as e:
        logger.error(f"Failed to start CTS sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/trigger-emails")
async def trigger_personalized_emails(
    email: Optional[str] = Query(None, description="Trigger for specific email only")
):
    """
    Manually trigger the delivery of personalized job emails.
    If email is provided, only that user receives it.
    """
    try:
        scheduler = get_scheduler()
        scheduler.trigger_manual_email_delivery(email=email)
        return {"message": f"Personalized email delivery triggered {'for ' + email if email else 'for all subscribers'}"}
    except Exception as e:
        logger.error(f"Failed to trigger emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
