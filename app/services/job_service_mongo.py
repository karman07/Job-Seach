from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from app.models import Job, JobSyncLog, Favorite, Bookmark, EmailSubscription
from app.integrations.adzuna import AdzunaClient
from app.config import get_settings
from bson import ObjectId
import uuid
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()


class JobService:
    """Service for managing jobs with MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.jobs_collection = db.jobs
        self.job_types_collection = db.job_types
        self.sync_logs_collection = db.job_sync_logs
        self.favorites_collection = db.favorites
        self.bookmarks_collection = db.bookmarks
        self.email_subscriptions_collection = db.email_subscriptions
        self.adzuna_client = AdzunaClient()
    
    async def sync_jobs_from_adzuna(
        self,
        sync_type: str = "manual",
        max_pages: int = 20,
        search_query: Optional[str] = None
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
                max_pages=max_pages,
                what=search_query
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
                    
                    # Extract and save job type
                    # Use search_query as the canonical type if available (e.g. "Civil Engineer")
                    # Otherwise fall back to category or title
                    type_to_save = search_query if search_query else (parsed_job.get("category") or parsed_job.get("title"))
                    
                    if type_to_save:
                        # Normalize to Title Case
                        type_to_save = type_to_save.title()
                        
                        # Save to job_types collection
                        await self.job_types_collection.update_one(
                            {"name": type_to_save}, 
                            {"$set": {"name": type_to_save, "category": parsed_job.get("category")}}, 
                            upsert=True
                        )
                
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
        """Create new job in DB"""
        try:
            # Generate unique requisition ID locally
            requisition_id = f"req-{job_data['adzuna_id']}-{uuid.uuid4().hex[:8]}"
            
            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(days=settings.JOB_EXPIRY_DAYS)
            
            # Create job model
            job = Job(
                adzuna_id=job_data["adzuna_id"],
                cts_job_name=None,
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
                last_synced_to_cts=None,
                raw_data=job_data.get("raw_data")
            )
            
            # Insert into MongoDB
            await self.jobs_collection.insert_one(job.dict(by_alias=True, exclude_none=True))
            
            logger.debug(f"Created job: {job.title}")
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    async def _update_job(self, existing_job: Dict[str, Any], job_data: Dict[str, Any]):
        """Update existing job in DB"""
        try:
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

    async def get_engineering_job_types(self) -> List[str]:
        """Get all stored engineering job types"""
        cursor = self.job_types_collection.find({}, {"name": 1, "_id": 0})
        types = await cursor.to_list(length=1000)
        return sorted([t["name"] for t in types if t.get("name")])

    async def delete_jobs_not_updated_since(self, timestamp: datetime) -> int:
        """Delete jobs that haven't been updated since the given timestamp"""
        try:
            result = await self.jobs_collection.delete_many({
                "updated_at": {"$lt": timestamp}
            })
            count = result.deleted_count
            logger.info(f"Deleted {count} old jobs not updated since {timestamp}")
            return count
        except Exception as e:
            logger.error(f"Error deleting old jobs: {str(e)}")
            return 0

    async def sync_engineering_jobs(self) -> JobSyncLog:
        """
        Sync top 10 engineering job types and delete old jobs (Daily Refresh).
        Target: ~5000 jobs.
        """
        # Clear existing polluted job types to ensure only generic types remain
        await self.job_types_collection.delete_many({})
        logger.info("Cleared job_types collection")

        # Top 10 Engineering Fields (10 pages each * 50 = 500 jobs/type => 5000 total)
        ENGINEERING_CONFIG = {
            "Software Engineer": 10,
            "Data Engineer": 10,
            "Civil Engineer": 10,
            "Mechanical Engineer": 10,
            "Electrical Engineer": 10,
            "Electronics Engineer": 10,
            "Computer Engineer": 10,
            "Chemical Engineer": 10,
            "Aerospace Engineer": 10,
            "Industrial Engineer": 10
        }
        
        start_time = datetime.utcnow()
        logger.info(f"Starting daily engineering sync at {start_time}")
        
        total_created = 0
        total_updated = 0
        total_failed = 0
        
        # Create a parent sync log
        sync_log = JobSyncLog(
            sync_type="daily_engineering_mass_sync",
            status="in_progress"
        )
        result = await self.sync_logs_collection.insert_one(sync_log.dict(by_alias=True))
        sync_log_id = result.inserted_id
        
        try:
            for query, pages in ENGINEERING_CONFIG.items():
                try:
                    logger.info(f"Mass Sync: Processing {query} (max_pages={pages})")
                    # We reuse sync_jobs_from_adzuna but capture its stats
                    # Note: We don't use its return value to update the main log yet
                    single_log = await self.sync_jobs_from_adzuna(
                        sync_type="manual_subtask",
                        max_pages=pages,
                        search_query=query
                    )
                    total_created += single_log.jobs_created
                    total_updated += single_log.jobs_updated
                    total_failed += single_log.jobs_failed
                    
                except Exception as e:
                    logger.error(f"Failed sub-sync for {query}: {str(e)}")
                    total_failed += 1
                
                # Pause to respect Rate Limits
                await asyncio.sleep(2)
            
            # Delete old jobs
            deleted_count = await self.delete_jobs_not_updated_since(start_time)
            
            # Update main log
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {
                    "$set": {
                        "status": "completed",
                        "jobs_created": total_created,
                        "jobs_updated": total_updated,
                        "jobs_deleted": deleted_count,
                        "jobs_failed": total_failed,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            updated_log = await self.sync_logs_collection.find_one({"_id": sync_log_id})
            return JobSyncLog(**updated_log) 
            
        except Exception as e:
            logger.error(f"Mass sync failed: {str(e)}")
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

    async def toggle_favorite(self, user_id: str, job_id: str) -> bool:
        """
        Toggle favorite status for a job
        Returns True if favorited, False if unfavorited
        """
        existing = await self.favorites_collection.find_one({
            "user_id": user_id,
            "job_id": job_id
        })
        
        if existing:
            await self.favorites_collection.delete_one({"_id": existing["_id"]})
            return False
        else:
            favorite = Favorite(user_id=user_id, job_id=job_id)
            await self.favorites_collection.insert_one(favorite.dict(by_alias=True))
            return True

    async def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all favorite jobs for a user"""
        cursor = self.favorites_collection.find({"user_id": user_id})
        favorites = await cursor.to_list(length=1000)
        
        job_ids = [ObjectId(f["job_id"]) for f in favorites]
        if not job_ids:
            return []
            
        cursor = self.jobs_collection.find({"_id": {"$in": job_ids}})
        return await cursor.to_list(length=1000)

    async def toggle_bookmark(self, user_id: str, job_id: str) -> bool:
        """
        Toggle bookmark status for a job
        Returns True if bookmarked, False if unbookmarked
        """
        existing = await self.bookmarks_collection.find_one({
            "user_id": user_id,
            "job_id": job_id
        })
        
        if existing:
            await self.bookmarks_collection.delete_one({"_id": existing["_id"]})
            return False
        else:
            bookmark = Bookmark(user_id=user_id, job_id=job_id)
            await self.bookmarks_collection.insert_one(bookmark.dict(by_alias=True))
            return True

    async def get_user_bookmarks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bookmarked jobs for a user"""
        cursor = self.bookmarks_collection.find({"user_id": user_id})
        bookmarks = await cursor.to_list(length=1000)
        
        job_ids = [ObjectId(b["job_id"]) for b in bookmarks]
        if not job_ids:
            return []
            
        cursor = self.jobs_collection.find({"_id": {"$in": job_ids}})
        return await cursor.to_list(length=1000)

    async def subscribe_email(
        self, 
        email: str, 
        resume_text: str,
        frequency: str = "biweekly", 
        is_enabled: bool = True,
        location: Optional[str] = None,
        internship_only: bool = False,
        job_level: Optional[str] = None,
        stipend_min: Optional[float] = None
    ) -> bool:
        """
        Record user email subscription with resume and preferences
        Returns True if newly subscribed/updated, False on failure
        """
        from datetime import datetime
        
        existing = await self.email_subscriptions_collection.find_one({"email": email})
        
        update_data = {
            "resume_text": resume_text,
            "frequency": frequency,
            "is_enabled": is_enabled,
            "location": location,
            "internship_only": internship_only,
            "job_level": job_level,
            "stipend_min": stipend_min,
            "updated_at": datetime.utcnow()
        }
        
        if existing:
            await self.email_subscriptions_collection.update_one(
                {"email": email},
                {"$set": update_data}
            )
            return True
            
        subscription = EmailSubscription(
            email=email,
            resume_text=resume_text,
            frequency=frequency,
            is_enabled=is_enabled,
            location=location,
            internship_only=internship_only,
            job_level=job_level,
            stipend_min=stipend_min
        )
        await self.email_subscriptions_collection.insert_one(subscription.dict(by_alias=True))
        return True

    async def get_all_subscriptions(self, frequency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active subscribed emails, optionally filtered by frequency"""
        query = {"is_enabled": True}
        if frequency:
            query["frequency"] = frequency
            
        cursor = self.email_subscriptions_collection.find(query)
        return await cursor.to_list(length=10000)

    async def unsubscribe_email(self, email: str) -> bool:
        """Remove email from subscriptions"""
        result = await self.email_subscriptions_collection.delete_one({"email": email})
        return result.deleted_count > 0

    async def get_personalized_jobs(self, email: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest top jobs for a user based on their favorites/bookmarks or generic top jobs.
        For simplicity, if no favorites, return top 5 recent jobs.
        """
        # In a real app, we'd look up the user by email first to get their user_id.
        # Here we'll return top 5 recent active jobs as a 'personalized' fallback.
        cursor = self.jobs_collection.find({"status": "active"}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
