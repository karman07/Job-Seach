from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import time
import logging
from app.database import get_db
from app.schemas import (
    ResumeMatchRequest, 
    JobDescriptionMatchRequest,
    JobMatchResponse,
    MatchResultResponse,
    JobListResponse,
    JobLevel
)
from app.services.matching_service_mongo import MatchingService
from app.services.job_service_mongo import JobService
from app.utils.resume_parser import ResumeParser

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/match/resume/upload", response_model=MatchResultResponse)
async def match_resume_by_upload(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    location: Optional[str] = Query(None, description="Preferred location"),
    internship_only: Optional[bool] = Query(False, description="Filter for internships only"),
    job_level: Optional[JobLevel] = Query(None, description="Preferred job level"),
    stipend_min: Optional[float] = Query(None, ge=0, description="Minimum salary/stipend"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Match jobs based on an uploaded resume file
    
    Upload your resume in PDF, DOCX, or TXT format and get matched jobs.
    
    **File Requirements:**
    - Formats: PDF (.pdf), Word (.docx), or Text (.txt)
    - Max size: 10MB
    - Minimum content: 50 characters
    
    **Query Parameters:**
    - **location**: Preferred job location (optional)
    - **internship_only**: Filter for internships only (optional, default: false)
    - **job_level**: Preferred job level - ENTRY_LEVEL, MID_LEVEL, SENIOR_LEVEL, EXECUTIVE (optional)
    - **stipend_min**: Minimum salary/stipend (optional)
    
    **Returns:**
    - Ranked list of matching jobs with relevance scores
    - Search metadata and timing information
    """
    try:
        start_time = time.time()
        
        # Parse resume from uploaded file
        logger.info(f"Processing resume upload: {file.filename}")
        resume_text = await ResumeParser.parse_resume(file)
        
        # Use matching service to find jobs
        matching_service = MatchingService(db)
        
        matched_jobs = await matching_service.match_resume_to_jobs(
            resume_text=resume_text,
            location=location,
            internship_only=internship_only,
            job_level=job_level.value if job_level else None,
            stipend_min=stipend_min,
            max_results=50
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Resume file match completed: {file.filename} -> {len(matched_jobs)} results in {search_time_ms:.2f}ms"
        )
        
        return MatchResultResponse(
            total_matches=len(matched_jobs),
            search_time_ms=search_time_ms,
            jobs=matched_jobs,
            metadata={
                "filename": file.filename,
                "file_type": file.content_type,
                "location": location,
                "internship_only": internship_only,
                "job_level": job_level.value if job_level else None,
                "stipend_min": stipend_min
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume file matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.post("/match/resume", response_model=MatchResultResponse)
async def match_resume(
    request: ResumeMatchRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Match a resume to relevant jobs using Google Cloud Talent Solution
    
    - **resume_text**: Full resume text (required)
    - **location**: Preferred location (optional)
    - **internship_only**: Filter for internships only (optional)
    - **job_level**: Preferred job level (optional)
    - **stipend_min**: Minimum salary/stipend (optional)
    
    Returns ranked jobs with CTS relevance scores
    """
    try:
        start_time = time.time()
        
        matching_service = MatchingService(db)
        
        # Perform matching
        matched_jobs = await matching_service.match_resume_to_jobs(
            resume_text=request.resume_text,
            location=request.location,
            internship_only=request.internship_only,
            job_level=request.job_level.value if request.job_level else None,
            stipend_min=request.stipend_min,
            max_results=50
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Resume match completed: {len(matched_jobs)} results in {search_time_ms:.2f}ms"
        )
        
        return MatchResultResponse(
            total_matches=len(matched_jobs),
            search_time_ms=search_time_ms,
            jobs=matched_jobs,
            metadata={
                "location": request.location,
                "internship_only": request.internship_only,
                "job_level": request.job_level.value if request.job_level else None
            }
        )
        
    except Exception as e:
        logger.error(f"Resume matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.post("/match/jd", response_model=MatchResultResponse)
async def match_job_description(
    request: JobDescriptionMatchRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Find similar jobs based on a job description
    
    - **job_description**: Job description text (required)
    - **location**: Location filter (optional)
    - **job_type**: Employment type filter (optional)
    
    Returns similar jobs from the database
    """
    try:
        start_time = time.time()
        
        matching_service = MatchingService(db)
        
        # Perform matching
        matched_jobs = await matching_service.match_jd_to_jobs(
            job_description=request.job_description,
            location=request.location,
            job_type=request.job_type.value if request.job_type else None,
            max_results=50
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"JD match completed: {len(matched_jobs)} results in {search_time_ms:.2f}ms"
        )
        
        return MatchResultResponse(
            total_matches=len(matched_jobs),
            search_time_ms=search_time_ms,
            jobs=matched_jobs,
            metadata={
                "location": request.location,
                "job_type": request.job_type.value if request.job_type else None
            }
        )
        
    except Exception as e:
        logger.error(f"JD matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.get("/jobs", response_model=JobListResponse)
async def get_jobs(
    min_stipend: float = None,
    max_stipend: float = None,
    remote: bool = None,
    internship: bool = None,
    location: str = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get jobs with optional filters
    
    Query parameters (all optional):
    - **min_stipend**: Minimum salary/stipend
    - **max_stipend**: Maximum salary/stipend
    - **remote**: Filter for remote jobs
    - **internship**: Filter for internships
    - **location**: Location filter (partial match)
    - **skip**: Pagination offset
    - **limit**: Results per page (max 100)
    """
    try:
        job_service = JobService(db)
        
        jobs, total = await job_service.get_jobs_with_filters(
            min_stipend=min_stipend,
            max_stipend=max_stipend,
            remote=remote,
            internship=internship,
            location=location,
            skip=skip,
            limit=min(limit, 100)
        )
        
        # Convert to response format
        job_responses = []
        for job in jobs:
            description = job.get("description", "")
            truncated_desc = description[:500] + "..." if len(description) > 500 else description
            
            job_response = JobMatchResponse(
                job_id=str(job["_id"]),
                adzuna_id=job["adzuna_id"],
                title=job["title"],
                company=job.get("company_display_name") or "Unknown",
                location=job.get("location"),
                employment_type=job.get("employment_type"),
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                description=truncated_desc,
                redirect_url=job.get("redirect_url"),
                relevance_score=0.0,  # No scoring for filtered results
                is_internship=job.get("is_internship", False)
            )
            job_responses.append(job_response)
        
        logger.info(f"Jobs query: returned {len(job_responses)} of {total} total")
        
        return JobListResponse(
            total=total,
            jobs=job_responses
        )
        
    except Exception as e:
        logger.error(f"Job listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")
