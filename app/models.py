from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, Dict, Any, List, Annotated
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(str))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema_: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class Company(BaseModel):
    """Company model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    cts_company_name: str
    display_name: str
    external_id: str
    website_uri: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """Job model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # External IDs
    adzuna_id: str
    cts_job_name: Optional[str] = None
    requisition_id: str
    
    # Job Details
    title: str
    description: str
    company_id: Optional[str] = None
    company_display_name: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    location_structured: Optional[Dict[str, Any]] = None
    
    # Employment
    employment_type: Optional[str] = None
    job_level: Optional[str] = None
    
    # Compensation
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    
    # Metadata
    category: Optional[str] = None
    contract_time: Optional[str] = None
    redirect_url: Optional[str] = None
    
    # Status
    status: str = "active"  # active, expired, deleted
    is_internship: bool = False
    is_remote: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_synced_to_cts: Optional[datetime] = None
    
    # Raw data
    raw_data: Optional[Dict[str, Any]] = None


class JobSyncLog(BaseModel):
    """Job sync log model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    sync_type: str  # daily_refresh, manual, initial
    status: str = "pending"  # pending, in_progress, completed, failed
    
    jobs_fetched: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_deleted: int = 0
    jobs_failed: int = 0
    
    search_query: Optional[str] = None
    country: Optional[str] = None
    error_message: Optional[str] = None
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ResumeSearchCache(BaseModel):
    """Resume search cache model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    resume_hash: str
    
    # Search parameters
    location: Optional[str] = None
    internship_only: Optional[bool] = None
    job_level: Optional[str] = None
    stipend_min: Optional[float] = None
    
    # Results
    matched_jobs: List[Dict[str, Any]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class Favorite(BaseModel):
    """Favorite model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    job_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Bookmark(BaseModel):
    """Bookmark model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    job_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmailSubscription(BaseModel):
    """EmailSubscription model for MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: str
    resume_text: str  # User's resume content for job matching
    frequency: str = "biweekly"  # daily, weekly, biweekly
    is_enabled: bool = True
    
    # Optional user preferences
    location: Optional[str] = None
    internship_only: bool = False
    job_level: Optional[str] = None  # ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE
    stipend_min: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
