from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging
from app.database import get_db
from app.schemas import HealthResponse
from app.integrations.cts import CTSClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Health check endpoint
    
    Verifies:
    - API is running
    - MongoDB connection is healthy
    - CTS connection is available
    """
    # Check MongoDB
    db_status = "healthy"
    try:
        await db.command("ping")
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Check CTS connection
    cts_status = "healthy"
    try:
        cts_client = CTSClient()
        # Try to list companies as a connection test
        cts_client.list_companies()
    except Exception as e:
        logger.error(f"CTS health check failed: {str(e)}")
        cts_status = "unhealthy"
    
    # Overall status
    status = "healthy" if db_status == "healthy" and cts_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database=db_status,
        cts_connection=cts_status
    )


@router.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Job Matching API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "resume_matching": "POST /match/resume",
            "jd_matching": "POST /match/jd",
            "job_listing": "GET /jobs",
            "manual_refresh": "POST /admin/refresh-jobs",
            "health": "GET /health"
        }
    }
