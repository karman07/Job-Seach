from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from app.config import get_settings
from app.database import get_database
from app.services.job_service_mongo import JobService

logger = logging.getLogger(__name__)
settings = get_settings()


class JobScheduler:
    """Scheduler for automated job refresh"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def refresh_jobs_task(self):
        """Background task to refresh jobs from Adzuna"""
        logger.info("Starting scheduled job refresh")
        db = await get_database()
        
        try:
            job_service = JobService(db)
            sync_log = await job_service.sync_jobs_from_adzuna(
                sync_type="daily_refresh",
                max_pages=30  # Fetch more pages for daily refresh
            )
            
            logger.info(
                f"Scheduled job refresh completed: "
                f"created={sync_log.jobs_created}, "
                f"updated={sync_log.jobs_updated}, "
                f"expired={sync_log.jobs_deleted}"
            )
        except Exception as e:
            logger.error(f"Scheduled job refresh failed: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Parse refresh time from settings (HH:MM format)
        try:
            hour, minute = settings.JOB_REFRESH_TIME.split(":")
            hour = int(hour)
            minute = int(minute)
        except Exception as e:
            logger.error(f"Invalid JOB_REFRESH_TIME format: {settings.JOB_REFRESH_TIME}")
            hour, minute = 3, 0  # Default to 3:00 AM
        
        # Add job to run daily at specified time
        self.scheduler.add_job(
            self.refresh_jobs_task,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_job_refresh",
            name="Daily Job Refresh from Adzuna",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"Job scheduler started. Daily refresh at {hour:02d}:{minute:02d} UTC"
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Job scheduler stopped")
    
    def trigger_manual_refresh(self):
        """Trigger an immediate job refresh (for admin endpoint)"""
        self.scheduler.add_job(
            self.refresh_jobs_task,
            trigger='date',
            run_date=datetime.now(),
            id=f"manual_refresh_{datetime.now().timestamp()}",
            replace_existing=False
        )
        logger.info("Manual job refresh triggered")


# Global scheduler instance
scheduler = JobScheduler()


def get_scheduler() -> JobScheduler:
    """Get the global scheduler instance"""
    return scheduler
