from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from app.config import get_settings
from app.database import get_database
from app.services.job_service_mongo import JobService
from app.utils.email_service import EmailService

logger = logging.getLogger(__name__)
settings = get_settings()


class JobScheduler:
    """Scheduler for automated job refresh"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def send_personalized_emails_task(self, frequency: Optional[str] = None, email: Optional[str] = None):
        """Background task to send top job suggestions based on subscriber's resume"""
        logger.info(f"Starting scheduled personalized email delivery (freq={frequency or 'ALL'}, email={email or 'ALL'})")
        db = await get_database()
        
        try:
            job_service = JobService(db)
            from app.services.matching_service_mongo import MatchingService
            matching_service = MatchingService(db)
            
            if email:
                # Get specific subscription
                subscription = await job_service.email_subscriptions_collection.find_one({"email": email})
                subscriptions = [subscription] if subscription else []
            else:
                subscriptions = await job_service.get_all_subscriptions(frequency=frequency)
            
            for sub in subscriptions:
                sub_email = sub["email"]
                resume_text = sub.get("resume_text", "")
                
                if not resume_text:
                    logger.warning(f"No resume found for {sub_email}, skipping")
                    continue
                
                # Match jobs based on resume and preferences
                try:
                    matched_jobs = await matching_service.match_resume_to_jobs(
                        resume_text=resume_text,
                        location=sub.get("location"),
                        internship_only=sub.get("internship_only", False),
                        job_level=sub.get("job_level"),
                        stipend_min=sub.get("stipend_min")
                    )
                    
                    if not matched_jobs or len(matched_jobs) == 0:
                        logger.info(f"No matching jobs found for {sub_email}")
                        continue
                    
                    # Take top 10 jobs
                    top_jobs = matched_jobs[:10]
                    
                    # Create HTML email body
                    job_list_html = "<ul style='list-style-type: none; padding: 0;'>"
                    for job in top_jobs:
                        job_list_html += f"""
                        <li style='margin-bottom: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                            <h3 style='margin: 0 0 10px 0; color: #1a202c; font-size: 18px;'>{job.title}</h3>
                            <p style='margin: 5px 0; color: #4a5568;'><strong>Company:</strong> {job.company or 'Unknown'}</p>
                            <p style='margin: 5px 0; color: #4a5568;'><strong>Location:</strong> {job.location or 'Not specified'}</p>
                            <a href='{job.redirect_url or '#'}' style='display: inline-block; margin-top: 15px; padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold;'>View Job Details</a>
                        </li>
                        """
                    job_list_html += "</ul>"
                    
                    body_html = f"""
                    <html>
                    <body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
                        <h2 style='color: #2c3e50;'>Your Personalized Job Matches</h2>
                        <p>Based on your resume and preferences, here are the top {len(top_jobs)} job opportunities for you:</p>
                        {job_list_html}
                        <hr style='margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;'>
                        <p style='font-size: 12px; color: #95a5a6;'>
                            You're receiving this because you subscribed to job alerts at aiforjob.ai<br>
                            <a href='#' style='color: #3498db;'>Update preferences</a> | <a href='#' style='color: #e74c3c;'>Unsubscribe</a>
                        </p>
                    </body>
                    </html>
                    """
                    
                    EmailService.send_email(
                        to_email=sub_email,
                        subject=f"🎯 {len(top_jobs)} Personalized Job Matches for You",
                        body_html=body_html
                    )
                    logger.info(f"Sent {len(top_jobs)} job matches to {sub_email}")
                    
                except Exception as e:
                    logger.error(f"Error matching jobs for {sub_email}: {str(e)}")
                    continue
                
            logger.info(f"Personalized email delivery completed for {len(subscriptions)} users")
        except Exception as e:
            logger.error(f"Personalized email delivery failed: {str(e)}")

    async def refresh_jobs_task(self):
        """Background task to refresh jobs from Adzuna"""
        logger.info("Starting scheduled job refresh")
        db = await get_database()
        
        try:
            job_service = JobService(db)
            sync_log = await job_service.sync_engineering_jobs()
            
            logger.info(
                f"Scheduled job refresh completed: "
                f"created={sync_log.jobs_created}, "
                f"updated={sync_log.jobs_updated}, "
                f"expired={sync_log.jobs_deleted}"
            )
        except Exception as e:
            logger.error(f"Scheduled job refresh failed: {str(e)}")
    
    async def start(self):
        """Start the background scheduler"""
        if self.is_running:
            return
            
        # Parse refresh time from settings (HH:MM format) or use defaults
        try:
            hour, minute = settings.JOB_REFRESH_TIME.split(":")
            hour = int(hour)
            minute = int(minute)
        except Exception:
            hour, minute = 2, 0 # Default to 2 AM UTC
            
        # 1. Daily Job Sync (runs at specified time)
        self.scheduler.add_job(
            self.refresh_jobs_task,
            CronTrigger(hour=hour, minute=minute),
            id='daily_job_sync',
            replace_existing=True
        )
        
        # 2. Daily Emails (runs at 10 AM UTC)
        self.scheduler.add_job(
            self.send_personalized_emails_task,
            CronTrigger(hour=10, minute=0),
            kwargs={"frequency": "daily"},
            id='daily_emails',
            replace_existing=True
        )
        
        # 3. Weekly Emails (runs on Tuesdays at 10 AM UTC)
        self.scheduler.add_job(
            self.send_personalized_emails_task,
            CronTrigger(day_of_week='tue', hour=10, minute=0),
            kwargs={"frequency": "weekly"},
            id='weekly_emails',
            replace_existing=True
        )
        
        # 4. Bi-weekly Emails (runs on Tuesdays and Thursdays at 10 AM UTC)
        self.scheduler.add_job(
            self.send_personalized_emails_task,
            CronTrigger(day_of_week='tue,thu', hour=10, minute=0),
            kwargs={"frequency": "biweekly"},
            id='biweekly_emails',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"Scheduler started (Daily sync at {hour:02d}:{minute:02d} UTC)")
    
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


    def trigger_manual_email_delivery(self, email: Optional[str] = None):
        """Trigger an immediate personalized email delivery (for admin endpoint)"""
        # Execute as a one-off job in the existing scheduler
        self.scheduler.add_job(
            self.send_personalized_emails_task,
            trigger='date',
            run_date=datetime.now(),
            kwargs={"email": email},
            id=f"manual_email_{datetime.now().timestamp()}",
            replace_existing=False
        )
        logger.info(f"Manual personalized email delivery triggered {'for ' + email if email else 'for all subscribers'}")


# Global scheduler instance
scheduler = JobScheduler()


def get_scheduler() -> JobScheduler:
    """Get the global scheduler instance"""
    return scheduler
