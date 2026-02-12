from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobLevel(str, Enum):
    ENTRY_LEVEL = "ENTRY_LEVEL"
    MID_LEVEL = "MID_LEVEL"
    SENIOR_LEVEL = "SENIOR_LEVEL"
    EXECUTIVE = "EXECUTIVE"


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACTOR = "CONTRACTOR"
    INTERNSHIP = "INTERNSHIP"


# Request Schemas
class ResumeMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, description="Full resume text")
    location: Optional[str] = Field(None, description="Preferred location")
    internship_only: Optional[bool] = Field(False, description="Filter for internships only")
    job_level: Optional[JobLevel] = Field(None, description="Preferred job level")
    stipend_min: Optional[float] = Field(None, ge=0, description="Minimum salary/stipend")
    
    @validator('resume_text')
    def validate_resume_text(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Resume text must be at least 50 characters')
        return v.strip()


class JobDescriptionMatchRequest(BaseModel):
    job_description: str = Field(..., min_length=50, description="Job description text")
    location: Optional[str] = Field(None, description="Location filter")
    job_type: Optional[EmploymentType] = Field(None, description="Employment type filter")
    
    @validator('job_description')
    def validate_jd_text(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters')
        return v.strip()


class UserJobInteractionRequest(BaseModel):
    user_id: str = Field(..., description="Unique ID of the user")


class UserJobInteractionResponse(BaseModel):
    message: str
    status: str
    is_active: bool  # True if favorited/bookmarked, False if removed


class EmailSubscriptionRequest(BaseModel):
    email: str = Field(..., description="Email address of the user")
    resume_text: str = Field(..., description="Resume content for job matching")
    frequency: Optional[str] = Field("biweekly", description="Notification frequency: daily, weekly, or biweekly")
    is_enabled: Optional[bool] = Field(True, description="Enable or disable notifications")
    
    # Optional user preferences
    location: Optional[str] = Field(None, description="Preferred job location")
    internship_only: Optional[bool] = Field(False, description="Filter for internships only")
    job_level: Optional[str] = Field(None, description="Preferred job level: ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE")
    stipend_min: Optional[float] = Field(None, description="Minimum salary/stipend")
    
    @validator('email')
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError('Invalid email address')
        return v.strip().lower()
    
    @validator('resume_text')
    def validate_resume(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Resume must be at least 50 characters')
        return v.strip()

class SubscriptionInfo(BaseModel):
    email: str
    frequency: str
    is_enabled: bool
    created_at: datetime


# Response Schemas
class JobMatchResponse(BaseModel):
    job_id: str  # MongoDB ObjectId as string
    adzuna_id: str
    title: str
    company: str
    location: Optional[str]
    employment_type: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    description: str
    redirect_url: Optional[str]
    relevance_score: float = Field(..., description="CTS relevance score (0-1)")
    is_internship: bool
    
    class Config:
        from_attributes = True


class MatchResultResponse(BaseModel):
    total_matches: int
    search_time_ms: float
    jobs: List[JobMatchResponse]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobFilterParams(BaseModel):
    min_stipend: Optional[float] = Field(None, ge=0)
    max_stipend: Optional[float] = Field(None, ge=0)
    remote: Optional[bool] = Field(None)
    internship: Optional[bool] = Field(None)
    location: Optional[str] = Field(None)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobMatchResponse]


class RefreshJobsResponse(BaseModel):
    message: str
    sync_id: int
    status: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    cts_connection: str
    version: str = "1.0.0"
