from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from app.models import Job, JobSyncLog
from app.integrations.adzuna import AdzunaClient
from app.integrations.cts import CTSClient
from app.config import get_settings
from bson import ObjectId

logger = logging.getLogger(__name__)
settings = get_settings()


class JobService:
    """Service for managing jobs with MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.jobs_collection = db.jobs
        self.sync_logs_collection = db.job_sync_logs
        self.adzuna_client = AdzunaClient()
        self.cts_client = CTSClient()
    
    async def sync_jobs_from_adzuna(
        self,
        sync_type: str = "manual",
        max_pages: int = 20
    ) -> JobSyncLog:
        """
        Fetch jobs from Adzuna, save to DB, and sync to CTS
        
        Returns:
            JobSyncLog with sync statistics
        """
        # Create sync log
        sync_log = JobSyncLog(
            sync_type=sync_type,
            status="in_progress"
        )
        
        result = await self.sync_logs_collection.insert_one(sync_log.dict(by_alias=True))
        sync_log_id = result.inserted_id
        
        try:
            logger.info(f"Starting job sync: type={sync_type}")
            
            # Fetch jobs from Adzuna
            jobs_data = await self.adzuna_client.fetch_all_jobs(
                max_pages=max_pages
            )
            
            # Update sync log
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {"$set": {"jobs_fetched": len(jobs_data)}}
            )
            
            logger.info(f"Fetched {len(jobs_data)} jobs from Adzuna")
            
            jobs_created = 0
            jobs_updated = 0
            jobs_failed = 0
            
            # Process each job
            for job_data in jobs_data:
                try:
                    parsed_job = self.adzuna_client.parse_job_data(job_data)
                    
                    # Check if job exists
                    existing_job = await self.jobs_collection.find_one(
                        {"adzuna_id": parsed_job["adzuna_id"]}
                    )
                    
                    if existing_job:
                        # Update existing job
                        await self._update_job(existing_job, parsed_job)
                        jobs_updated += 1
                    else:
                        # Create new job
                        await self._create_job(parsed_job)
                        jobs_created += 1
                
                except Exception as e:
                    logger.error(f"Error processing job {job_data.get('id')}: {str(e)}")
                    jobs_failed += 1
            
            # Mark old jobs as expired
            expired_count = await self._mark_expired_jobs()
            
            # Complete sync
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {
                    "$set": {
                        "status": "completed",
                        "jobs_created": jobs_created,
                        "jobs_updated": jobs_updated,
                        "jobs_deleted": expired_count,
                        "jobs_failed": jobs_failed,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(
                f"Sync completed: created={jobs_created}, "
                f"updated={jobs_updated}, expired={expired_count}, "
                f"failed={jobs_failed}"
            )
            
            # Return updated sync log
            updated_log = await self.sync_logs_collection.find_one({"_id": sync_log_id})
            return JobSyncLog(**updated_log)
            
        except Exception as e:
            logger.error(f"Job sync failed: {str(e)}")
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            raise
    
    async def _create_job(self, job_data: Dict[str, Any]):
        """Create new job in DB and CTS"""
        try:
            # Generate unique requisition ID
            requisition_id = self.cts_client.generate_requisition_id(job_data["adzuna_id"])
            
            # Try to create in CTS (will be skipped if permissions not enabled)
            cts_job_name = None
            try:
                cts_job_name = self.cts_client.create_job(job_data)
                logger.debug(f"Created job in CTS: {cts_job_name}")
            except Exception as e:
                logger.warning(f"CTS creation failed (job will still be stored in DB): {str(e)}")
            
            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(days=settings.JOB_EXPIRY_DAYS)
            
            # Create job model
            job = Job(
                adzuna_id=job_data["adzuna_id"],
                cts_job_name=cts_job_name,
                requisition_id=requisition_id,
                title=job_data["title"],
                description=job_data["description"],
                company_display_name=job_data.get("company_display_name"),
                location=job_data.get("location"),
                location_structured=job_data.get("location_structured"),
                employment_type=job_data.get("employment_type"),
                job_level=job_data.get("job_level"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                salary_currency=job_data.get("salary_currency", "USD"),
                category=job_data.get("category"),
                contract_time=job_data.get("contract_time"),
                redirect_url=job_data.get("redirect_url"),
                is_internship=job_data.get("is_internship", False),
                is_remote=job_data.get("is_remote", False),
                status="active",
                expires_at=expires_at,
                last_synced_to_cts=datetime.utcnow() if cts_job_name else None,
                raw_data=job_data.get("raw_data")
            )
            
            # Insert into MongoDB
            await self.jobs_collection.insert_one(job.dict(by_alias=True, exclude_none=True))
            
            logger.debug(f"Created job: {job.title}")
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    async def _update_job(self, existing_job: Dict[str, Any], job_data: Dict[str, Any]):
        """Update existing job in DB and CTS"""
        try:
            # Update CTS if job exists there
            if existing_job.get("cts_job_name"):
                try:
                    self.cts_client.update_job(existing_job["cts_job_name"], job_data)
                    last_synced = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Failed to update job in CTS: {str(e)}")
                    last_synced = existing_job.get("last_synced_to_cts")
            else:
                last_synced = None
            
            # Update database
            await self.jobs_collection.update_one(
                {"_id": existing_job["_id"]},
                {
                    "$set": {
                        "title": job_data["title"],
                        "description": job_data["description"],
                        "company_display_name": job_data.get("company_display_name"),
                        "location": job_data.get("location"),
                        "location_structured": job_data.get("location_structured"),
                        "employment_type": job_data.get("employment_type"),
                        "job_level": job_data.get("job_level"),
                        "salary_min": job_data.get("salary_min"),
                        "salary_max": job_data.get("salary_max"),
                        "category": job_data.get("category"),
                        "redirect_url": job_data.get("redirect_url"),
                        "is_internship": job_data.get("is_internship", False),
                        "is_remote": job_data.get("is_remote", False),
                        "status": "active",
                        "expires_at": datetime.utcnow() + timedelta(days=settings.JOB_EXPIRY_DAYS),
                        "updated_at": datetime.utcnow(),
                        "last_synced_to_cts": last_synced,
                        "raw_data": job_data.get("raw_data")
                    }
                }
            )
            
            logger.debug(f"Updated job: {job_data['title']}")
            
        except Exception as e:
            logger.error(f"Error updating job: {str(e)}")
            raise
    
    async def _mark_expired_jobs(self) -> int:
        """Mark jobs as expired if they're past expiry date"""
        try:
            result = await self.jobs_collection.update_many(
                {
                    "status": "active",
                    "expires_at": {"$lt": datetime.utcnow()}
                },
                {"$set": {"status": "expired"}}
            )
            
            count = result.modified_count
            
            if count > 0:
                logger.info(f"Marked {count} jobs as expired")
            
            return count
            
        except Exception as e:
            logger.error(f"Error marking expired jobs: {str(e)}")
            return 0
    
    async def get_jobs_with_filters(
        self,
        min_stipend: Optional[float] = None,
        max_stipend: Optional[float] = None,
        remote: Optional[bool] = None,
        internship: Optional[bool] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get jobs with optional filters
        
        Returns:
            Tuple of (jobs list, total count)
        """
        # Build query
        query = {"status": "active"}
        
        if min_stipend is not None:
            query["$or"] = [
                {"salary_min": {"$gte": min_stipend}},
                {"salary_max": {"$gte": min_stipend}}
            ]
        
        if max_stipend is not None:
            if "$or" not in query:
                query["$or"] = []
            query["$or"].extend([
                {"salary_min": {"$lte": max_stipend}},
                {"salary_max": {"$lte": max_stipend}}
            ])
        
        if remote is not None:
            query["is_remote"] = remote
        
        if internship is not None:
            query["is_internship"] = internship
        
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        
        # Get total count
        total = await self.jobs_collection.count_documents(query)
        
        # Get jobs
        cursor = self.jobs_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        jobs = await cursor.to_list(length=limit)
        
        return jobs, total
    
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        return await self.jobs_collection.find_one({
            "_id": ObjectId(job_id),
            "status": "active"
        })
    
    async def get_job_by_adzuna_id(self, adzuna_id: str) -> Optional[Dict[str, Any]]:
        """Get job by Adzuna ID"""
        return await self.jobs_collection.find_one({"adzuna_id": adzuna_id})
