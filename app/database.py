from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from typing import Optional
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global MongoDB client
mongodb_client: Optional[AsyncIOMotorClient] = None


async def get_database():
    """Get MongoDB database instance"""
    return mongodb_client[settings.MONGODB_DB_NAME]


async def connect_to_mongo():
    """Create MongoDB connection"""
    global mongodb_client
    try:
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000
        )
        # Test connection
        await mongodb_client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("Closed MongoDB connection")


async def create_indexes():
    """Create database indexes for performance"""
    try:
        db = await get_database()
        
        # Jobs collection indexes
        jobs_collection = db.jobs
        await jobs_collection.create_index("adzuna_id", unique=True)
        await jobs_collection.create_index("requisition_id", unique=True)
        await jobs_collection.create_index("status")
        await jobs_collection.create_index("expires_at")
        await jobs_collection.create_index([("location", ASCENDING), ("status", ASCENDING)])
        await jobs_collection.create_index([("is_internship", ASCENDING), ("status", ASCENDING)])
        await jobs_collection.create_index("created_at")
        # Text index for resume matching fallback
        await jobs_collection.create_index([
            ("title", "text"),
            ("description", "text"),
            ("company_display_name", "text")
        ], name="job_text_search")
        
        # Companies collection indexes
        companies_collection = db.companies
        await companies_collection.create_index("cts_company_name", unique=True)
        await companies_collection.create_index("external_id", unique=True)
        
        # Sync logs collection indexes
        sync_logs_collection = db.job_sync_logs
        await sync_logs_collection.create_index([("status", ASCENDING), ("started_at", DESCENDING)])
        
        # Cache collection indexes
        cache_collection = db.resume_search_cache
        await cache_collection.create_index("resume_hash")
        await cache_collection.create_index("expires_at")
        await cache_collection.create_index([("resume_hash", ASCENDING), ("expires_at", ASCENDING)])
        
        # Favorites collection indexes
        favorites_collection = db.favorites
        await favorites_collection.create_index([("user_id", ASCENDING), ("job_id", ASCENDING)], unique=True)
        await favorites_collection.create_index("user_id")
        
        # Bookmarks collection indexes
        bookmarks_collection = db.bookmarks
        await bookmarks_collection.create_index([("user_id", ASCENDING), ("job_id", ASCENDING)], unique=True)
        await bookmarks_collection.create_index("user_id")
        
        # Email subscriptions collection indexes
        email_subs_collection = db.email_subscriptions
        await email_subs_collection.create_index("email", unique=True)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")


async def get_db():
    """Dependency for FastAPI routes"""
    db = await get_database()
    try:
        yield db
    finally:
        pass  # Connection pooling handles cleanup
