from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.config import get_settings
from app.database import connect_to_mongo, close_mongo_connection
from app.scheduler import get_scheduler
from app.api import jobs, admin, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Job Matching API...")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected and indexes created")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
    
    # Start scheduler
    try:
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("Job scheduler started")
    except Exception as e:
        logger.error(f"Scheduler start failed: {str(e)}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Job Matching API...")
    
    # Stop scheduler
    try:
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("Job scheduler stopped")
    except Exception as e:
        logger.error(f"Scheduler stop failed: {str(e)}")
    
    # Close MongoDB connection
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"MongoDB close failed: {str(e)}")
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Job Matching API",
    description="Production-grade job matching backend using Adzuna and Google Cloud Talent Solution",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(jobs.router, tags=["Jobs"])
app.include_router(admin.router, tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
